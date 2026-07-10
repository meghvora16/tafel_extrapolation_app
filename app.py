import json
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np

from tafel_core.config import TafelConfig
from tafel_core.data_io import (
    read_uploaded_file,
    dataframe_to_csv_bytes,
    dataframe_to_excel_bytes,
    dict_to_json_bytes,
)
from tafel_core.fitting import TafelFitter
from tafel_core.plotting import create_interactive_plot
from tafel_core.validation import generate_quality_flags


# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="Advanced Tafel Extrapolation App",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Logo / Asset Paths
# ============================================================

APP_DIR = Path(__file__).resolve().parent
ASSETS_DIR = APP_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "schaeffler_logo.png"


# ============================================================
# Global Styling
# ============================================================

def inject_global_css():
    st.markdown(
        """
        <style>
        /* Main app spacing */
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        /* Sidebar polish */
        section[data-testid="stSidebar"] {
            background-color: #f4f6f8;
            border-right: 1px solid #e1e5ea;
        }

        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {
            color: #1f2933;
        }

        /* Hero card */
        .hero-card {
            padding: 2.1rem 2.3rem 2.0rem 2.3rem;
            margin-top: 0.6rem;
            margin-bottom: 1.6rem;
            border-radius: 22px;
            background:
                radial-gradient(circle at top right, rgba(0, 153, 76, 0.26), transparent 30%),
                linear-gradient(135deg, #050505 0%, #101820 48%, #004f2d 100%);
            border: 1px solid rgba(0, 153, 76, 0.45);
            box-shadow:
                0 16px 42px rgba(0, 0, 0, 0.26),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }

        .hero-kicker {
            color: #8be0b3;
            font-size: 0.84rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            margin-bottom: 0.65rem;
        }

        .hero-title {
            color: #ffffff;
            font-size: 2.55rem;
            font-weight: 800;
            letter-spacing: -0.035em;
            line-height: 1.08;
            max-width: 1100px;
            margin-bottom: 0.8rem;
        }

        .hero-subtitle {
            color: #d7e6dd;
            font-size: 1.08rem;
            line-height: 1.55;
            max-width: 1120px;
            margin-bottom: 1.0rem;
        }

        .hero-highlight {
            color: #ffffff;
            font-weight: 700;
        }

        .badge-row {
            display: flex;
            gap: 0.55rem;
            flex-wrap: wrap;
            margin-top: 1.05rem;
        }

        .hero-badge {
            color: #ffffff;
            background-color: rgba(0, 153, 76, 0.34);
            border: 1px solid rgba(116, 230, 168, 0.58);
            padding: 0.32rem 0.70rem;
            border-radius: 999px;
            font-size: 0.80rem;
            font-weight: 700;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
        }

        .intro-card {
            padding: 1.25rem 1.35rem;
            margin-bottom: 1.5rem;
            border-radius: 16px;
            background: #ffffff;
            border: 1px solid #e6e9ee;
            box-shadow: 0 4px 16px rgba(16, 24, 40, 0.06);
        }

        .intro-card p {
            margin-bottom: 0.7rem;
        }

        .section-heading {
            margin-top: 1.0rem;
            margin-bottom: 0.5rem;
            font-size: 1.35rem;
            font-weight: 750;
            color: #1f2933;
        }

        /* Metrics slight polish */
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e6e9ee;
            padding: 0.85rem 0.95rem;
            border-radius: 14px;
            box-shadow: 0 3px 12px rgba(16, 24, 40, 0.05);
        }

        @media screen and (max-width: 900px) {
            .hero-title {
                font-size: 1.95rem;
            }

            .hero-subtitle {
                font-size: 0.98rem;
            }

            .hero-card {
                padding: 1.55rem 1.45rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Header Helper
# ============================================================

def render_app_header():
    """
    Render a clean Schaeffler-branded application header.

    Logo location:
        assets/schaeffler_logo.png
    """

    # Logo row — centered, clean, outside HTML to avoid Streamlit rendering issues
    logo_left, logo_center, logo_right = st.columns([2.2, 1.2, 2.2])

    with logo_center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown(
                """
                <div style="
                    text-align:center;
                    color:#009944;
                    font-size:2.1rem;
                    font-weight:900;
                    letter-spacing:0.06em;
                    margin-bottom:0.7rem;
                ">
                    SCHAEFFLER
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-kicker">
                Schaeffler Electrochemical Analysis Platform
            </div>

            <div class="hero-title">
                Advanced Tafel Extrapolation & Polarization Curve Fitting
            </div>

            <div class="hero-subtitle">
                A professional analysis tool for
                <span class="hero-highlight">LSV polarization data</span>,
                corrosion parameter extraction, adaptive global fitting,
                passive/transpassive detection, and scalable batch evaluation.
            </div>

            <div class="badge-row">
                <span class="hero-badge">Anodic scans</span>
                <span class="hero-badge">Cathodic scans</span>
                <span class="hero-badge">Auto-detection</span>
                <span class="hero-badge">Classical Tafel</span>
                <span class="hero-badge">Global fitting</span>
                <span class="hero-badge">Hybrid workflow</span>
                <span class="hero-badge">Batch processing</span>
                <span class="hero-badge">Downloadable reports</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Helper functions
# ============================================================

def render_result(result):
    summary = result.summary

    st.subheader(f"📄 Result: `{summary['file_name']}`")

    flags = generate_quality_flags(summary)

    for flag in flags:
        if flag["level"] == "success":
            st.success(flag["message"])
        elif flag["level"] == "warning":
            st.warning(flag["message"])
        elif flag["level"] == "error":
            st.error(flag["message"])
        else:
            st.info(flag["message"])

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Ecorr final / V", f"{summary['Ecorr_final_V']:.4f}")
    c2.metric("Ecorr observed / V", f"{summary['Ecorr_observed_V']:.4f}")
    c3.metric(
        f"Icorr / {summary['current_unit']}",
        f"{summary['Icorr_abs']:.3e}",
    )
    c4.metric("ba / V dec⁻¹", f"{summary['ba_V_dec']:.4f}")
    c5.metric("bc / V dec⁻¹", f"{summary['bc_V_dec']:.4f}")

    c6, c7, c8, c9 = st.columns(4)

    c6.metric("R² global", f"{summary['R2_log_global']:.4f}")
    c7.metric("RMSE global", f"{summary['RMSE_log_global']:.4f}")
    c8.metric("Epp / V", f"{summary['Epp_V']:.4f}")

    eb = summary["Eb_V"]
    c9.metric("Eb / V", "not detected" if eb is None else f"{eb:.4f}")

    fig = create_interactive_plot(
        result,
        dark_theme=st.session_state.get("dark_theme", True),
    )

    st.plotly_chart(fig, use_container_width=True)

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "📋 Summary",
            "📉 Processed data",
            "📈 Dense fit",
            "🧪 Diagnostics",
        ]
    )

    with tab1:
        st.dataframe(pd.DataFrame([summary]), use_container_width=True)

        st.download_button(
            "Download summary JSON",
            data=dict_to_json_bytes(summary),
            file_name=f"{summary['file_name']}_summary.json",
            mime="application/json",
        )

    with tab2:
        st.dataframe(result.processed_df, use_container_width=True)

        st.download_button(
            "Download processed CSV",
            data=dataframe_to_csv_bytes(result.processed_df),
            file_name=f"{summary['file_name']}_processed.csv",
            mime="text/csv",
        )

    with tab3:
        st.dataframe(result.dense_df, use_container_width=True)

        st.download_button(
            "Download dense fit CSV",
            data=dataframe_to_csv_bytes(result.dense_df),
            file_name=f"{summary['file_name']}_dense_fit.csv",
            mime="text/csv",
        )

    with tab4:
        st.json(result.diagnostics)

        st.download_button(
            "Download diagnostics JSON",
            data=dict_to_json_bytes(result.diagnostics),
            file_name=f"{summary['file_name']}_diagnostics.json",
            mime="application/json",
        )


# ============================================================
# Inject CSS
# ============================================================

inject_global_css()


# ============================================================
# Sidebar
# ============================================================

# Important:
# The logo has intentionally been removed from the sidebar.

st.sidebar.header("⚙️ Main Settings")

processing_label = st.sidebar.selectbox(
    "Processing mode",
    [
        "Single uploaded file",
        "Multiple uploaded files",
        "Batch folder",
    ],
)

scan_label = st.sidebar.selectbox(
    "Scan fitting mode",
    [
        "Auto-detect",
        "Anodic scan",
        "Cathodic scan",
    ],
)

fit_label = st.sidebar.selectbox(
    "Fit strategy",
    [
        "Hybrid: global + Tafel extrapolation",
        "Classical Tafel only",
        "Global model only",
    ],
)

scan_mode_map = {
    "Auto-detect": "auto",
    "Anodic scan": "anodic",
    "Cathodic scan": "cathodic",
}

fit_strategy_map = {
    "Hybrid: global + Tafel extrapolation": "hybrid",
    "Classical Tafel only": "classical",
    "Global model only": "global",
}

scan_mode = scan_mode_map[scan_label]
fit_strategy = fit_strategy_map[fit_label]

st.sidebar.subheader("📌 Data Columns")

potential_col = st.sidebar.text_input(
    "Potential column",
    value="WE(1).Potential (V)",
)

current_col = st.sidebar.text_input(
    "Current column",
    value="WE(1).Current (A)",
)

use_area = st.sidebar.checkbox("Normalize current by electrode area", value=False)

area_cm2 = None

if use_area:
    area_cm2 = st.sidebar.number_input(
        "Electrode area / cm²",
        min_value=1e-12,
        value=1.0,
        step=0.1,
        format="%.8f",
    )

st.sidebar.subheader("📐 Tafel Windows")

auto_tafel_enabled = st.sidebar.checkbox(
    "Automatic Tafel-window search",
    value=True,
)

tafel_anodic_min_v = st.sidebar.number_input(
    "Manual anodic min from Ecorr / V",
    value=0.015,
    step=0.001,
    format="%.4f",
)

tafel_anodic_max_v = st.sidebar.number_input(
    "Manual anodic max from Ecorr / V",
    value=0.028,
    step=0.001,
    format="%.4f",
)

tafel_cathodic_min_v = st.sidebar.number_input(
    "Manual cathodic min from Ecorr / V",
    value=0.015,
    step=0.001,
    format="%.4f",
)

tafel_cathodic_max_v = st.sidebar.number_input(
    "Manual cathodic max from Ecorr / V",
    value=0.045,
    step=0.001,
    format="%.4f",
)

st.sidebar.subheader("🔒 Physical Bounds")

ba_min = st.sidebar.number_input(
    "ba min / V dec⁻¹",
    value=0.030,
    step=0.005,
    format="%.4f",
)

ba_max = st.sidebar.number_input(
    "ba max / V dec⁻¹",
    value=0.300,
    step=0.005,
    format="%.4f",
)

bc_min = st.sidebar.number_input(
    "bc min / V dec⁻¹",
    value=0.030,
    step=0.005,
    format="%.4f",
)

bc_max = st.sidebar.number_input(
    "bc max / V dec⁻¹",
    value=0.450,
    step=0.005,
    format="%.4f",
)

st.sidebar.subheader("🧮 Global Model")

passive_detection_enabled = st.sidebar.checkbox(
    "Enable passive-region detection",
    value=True,
)

transpassive_detection_enabled = st.sidebar.checkbox(
    "Enable transpassive detection",
    value=True,
)

manual_transpassive = st.sidebar.checkbox(
    "Use manual transpassive guess",
    value=False,
)

transpassive_guess_v = None

if manual_transpassive:
    transpassive_guess_v = st.sidebar.number_input(
        "Transpassive guess / V",
        value=0.8,
        step=0.01,
        format="%.4f",
    )

max_nfev = st.sidebar.number_input(
    "Max optimizer evaluations",
    min_value=1000,
    max_value=300000,
    value=140000,
    step=1000,
)

dense_points = st.sidebar.number_input(
    "Dense fit points",
    min_value=300,
    max_value=10000,
    value=1400,
    step=100,
)

st.sidebar.subheader("🎨 Plot Settings")

dark_theme = st.sidebar.checkbox("Dark theme", value=True)
st.session_state["dark_theme"] = dark_theme


# ============================================================
# Main Header
# ============================================================

render_app_header()


# ============================================================
# Intro Section
# ============================================================

st.markdown(
    """
    <div class="intro-card">
        <p>
            This application performs advanced Tafel extrapolation and global
            polarization-curve fitting for electrochemical LSV data.
        </p>

        <p>
            It supports anodic, cathodic, and automatically detected scan directions,
            classical Tafel extrapolation, adaptive nonlinear global fitting,
            passive/transpassive detection, and single-file or batch processing.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Configuration
# ============================================================

config = TafelConfig(
    potential_col=potential_col,
    current_col=current_col,
    area_cm2=area_cm2,
    scan_mode=scan_mode,
    fit_strategy=fit_strategy,
    tafel_anodic_min_v=tafel_anodic_min_v,
    tafel_anodic_max_v=tafel_anodic_max_v,
    tafel_cathodic_min_v=tafel_cathodic_min_v,
    tafel_cathodic_max_v=tafel_cathodic_max_v,
    auto_tafel_enabled=auto_tafel_enabled,
    ba_min_v_dec=ba_min,
    ba_max_v_dec=ba_max,
    bc_min_v_dec=bc_min,
    bc_max_v_dec=bc_max,
    passive_detection_enabled=passive_detection_enabled,
    transpassive_detection_enabled=transpassive_detection_enabled,
    transpassive_guess_v=transpassive_guess_v,
    max_nfev=int(max_nfev),
    dense_points=int(dense_points),
    dark_theme=dark_theme,
)

fitter = TafelFitter(config)


# ============================================================
# Processing Modes
# ============================================================

if processing_label == "Single uploaded file":
    st.markdown('<div class="section-heading">📤 Single File Analysis</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Upload one LSV file",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=False,
    )

    if uploaded_file is not None:
        st.info(f"Selected file: `{uploaded_file.name}`")

        if st.button("🚀 Run single fit", type="primary"):
            try:
                with st.spinner("Reading file..."):
                    df = read_uploaded_file(uploaded_file)

                with st.expander("Preview input data", expanded=False):
                    st.dataframe(df.head(100), use_container_width=True)

                with st.spinner("Running Tafel/global fit..."):
                    result = fitter.fit_dataframe(
                        df,
                        file_name=uploaded_file.name,
                    )

                st.success("Fit completed successfully.")
                render_result(result)

            except Exception as exc:
                st.error("Fit failed.")
                st.exception(exc)


elif processing_label == "Multiple uploaded files":
    st.markdown('<div class="section-heading">📤 Uploaded Batch Analysis</div>', unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "Upload multiple LSV files",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True,
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} file(s) uploaded.")

        if st.button("🚀 Run uploaded-file batch fit", type="primary"):
            results = []
            summaries = []

            progress = st.progress(0.0)

            for i, uploaded_file in enumerate(uploaded_files, start=1):
                st.divider()
                st.write(f"Processing `{uploaded_file.name}`")

                try:
                    df = read_uploaded_file(uploaded_file)

                    result = fitter.fit_dataframe(
                        df,
                        file_name=uploaded_file.name,
                    )

                    results.append(result)
                    summaries.append(result.summary)

                    render_result(result)

                except Exception as exc:
                    st.error(f"Fit failed for `{uploaded_file.name}`.")
                    st.exception(exc)

                progress.progress(i / len(uploaded_files))

            if summaries:
                st.header("📦 Batch Summary")

                batch_df = pd.DataFrame(summaries)
                st.dataframe(batch_df, use_container_width=True)

                st.download_button(
                    "Download batch summary CSV",
                    data=dataframe_to_csv_bytes(batch_df),
                    file_name="batch_fit_summary.csv",
                    mime="text/csv",
                )

                st.download_button(
                    "Download batch summary Excel",
                    data=dataframe_to_excel_bytes(
                        {"batch_summary": batch_df}
                    ),
                    file_name="batch_fit_summary.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )


elif processing_label == "Batch folder":
    st.markdown('<div class="section-heading">📁 Folder Batch Analysis</div>', unsafe_allow_html=True)

    st.warning(
        "Batch folder mode works only when Streamlit has access to the local or network folder path."
    )

    root_dir = st.text_input(
        "Root folder",
        value=r"C:\Users\VORAMGH\OneDrive - Schaeffler\Electrolyzer_EC",
    )

    target_filename = st.text_input(
        "Target filename",
        value="lsv.xlsx",
    )

    folder_filter = st.selectbox(
        "Folder filter",
        [
            "No filter",
            "Only folders containing (Anodic)",
            "Only folders containing (Cathodic)",
            "Custom keyword",
        ],
    )

    custom_keyword = ""

    if folder_filter == "Custom keyword":
        custom_keyword = st.text_input("Custom keyword", value="")

    if st.button("🚀 Run folder batch fit", type="primary"):
        root = Path(root_dir)

        if not root.exists():
            st.error(f"Root folder does not exist: `{root}`")
            st.stop()

        files = sorted(root.rglob(target_filename))

        if folder_filter == "Only folders containing (Anodic)":
            files = [fp for fp in files if "(Anodic)" in fp.parent.name]

        elif folder_filter == "Only folders containing (Cathodic)":
            files = [fp for fp in files if "(Cathodic)" in fp.parent.name]

        elif folder_filter == "Custom keyword":
            files = [fp for fp in files if custom_keyword in fp.parent.name]

        if not files:
            st.warning("No matching files found.")
            st.stop()

        st.info(f"Found {len(files)} matching file(s).")

        summaries = []
        progress = st.progress(0.0)

        for i, fp in enumerate(files, start=1):
            st.write(f"Processing `{fp}`")

            try:
                df = pd.read_excel(fp)

                result = fitter.fit_dataframe(
                    df,
                    file_name=str(fp),
                )

                summaries.append(result.summary)

                st.success(
                    f"OK: {fp.name} | "
                    f"Ecorr={result.summary['Ecorr_final_V']:.4f} V | "
                    f"Icorr={result.summary['Icorr_abs']:.3e}"
                )

            except Exception as exc:
                st.error(f"Failed: `{fp}`")
                st.exception(exc)

            progress.progress(i / len(files))

        if summaries:
            batch_df = pd.DataFrame(summaries)

            st.header("📦 Batch Summary")
            st.dataframe(batch_df, use_container_width=True)

            st.download_button(
                "Download batch summary CSV",
                data=dataframe_to_csv_bytes(batch_df),
                file_name="batch_fit_summary.csv",
                mime="text/csv",
            )

            st.download_button(
                "Download batch summary Excel",
                data=dataframe_to_excel_bytes(
                    {"batch_summary": batch_df}
                ),
                file_name="batch_fit_summary.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
            )
