import numpy as np
import plotly.graph_objects as go


def create_interactive_plot(result, dark_theme=True):
    summary = result.summary
    arrays = result.arrays
    tafel = arrays["tafel_result"]

    E = arrays["E"]
    ylog = arrays["ylog"]
    E_dense = arrays["E_dense"]
    y_dense = arrays["y_dense"]

    template = "plotly_dark" if dark_theme else "plotly_white"

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=E,
            y=ylog,
            mode="lines+markers",
            name="Measured",
            line=dict(width=2),
            marker=dict(size=4),
        )
    )

    if np.any(np.isfinite(y_dense)):
        fig.add_trace(
            go.Scatter(
                x=E_dense,
                y=y_dense,
                mode="lines",
                name=f"Global fit R²={summary['R2_log_global']:.4f}",
                line=dict(width=3),
            )
        )

    Ecorr_obs = arrays["Ecorr_obs"]
    Ecorr_final = arrays["Ecorr_final"]
    Icorr_final = arrays["Icorr_final"]

    fig.add_vline(
        x=Ecorr_obs,
        line_dash="dot",
        annotation_text=f"Ecorr obs {Ecorr_obs:.4f} V",
    )

    fig.add_vline(
        x=Ecorr_final,
        line_dash="dash",
        annotation_text=f"Ecorr final {Ecorr_final:.4f} V",
    )

    fig.add_trace(
        go.Scatter(
            x=[Ecorr_final],
            y=[np.log10(max(Icorr_final, 1e-30))],
            mode="markers",
            name=f"Icorr={Icorr_final:.3e}",
            marker=dict(size=14, symbol="x"),
        )
    )

    if tafel.get("tafel_ok", False):
        an = tafel["anodic_fit"]
        ca = tafel["cathodic_fit"]

        if an is not None:
            x_an = np.linspace(an["E_min"], an["E_max"], 100)
            y_an = an["slope"] * x_an + an["intercept"]

            fig.add_trace(
                go.Scatter(
                    x=x_an,
                    y=y_an,
                    mode="lines",
                    name=f"Anodic Tafel ba={summary['ba_V_dec']*1000:.0f} mV/dec",
                    line=dict(dash="dash"),
                )
            )

        if ca is not None:
            x_ca = np.linspace(ca["E_min"], ca["E_max"], 100)
            y_ca = ca["slope"] * x_ca + ca["intercept"]

            fig.add_trace(
                go.Scatter(
                    x=x_ca,
                    y=y_ca,
                    mode="lines",
                    name=f"Cathodic Tafel bc={summary['bc_V_dec']*1000:.0f} mV/dec",
                    line=dict(dash="dot"),
                )
            )

    if arrays["transpassive_exists"]:
        fig.add_vline(
            x=arrays["Etr"],
            line_dash="dashdot",
            annotation_text=f"Eb {arrays['Etr']:.4f} V",
        )

    yaxis_title = (
        "log10 |i| / A cm^-2"
        if summary["current_unit"] == "A cm^-2"
        else "log10 |I| / A"
    )

    fig.update_layout(
        template=template,
        title=(
            "Potentiodynamic Polarization Tafel Extrapolation<br>"
            f"{summary['scan_direction']} | {summary['fit_strategy']} | "
            f"Icorr={summary['Icorr_abs']:.3e} {summary['current_unit']}"
        ),
        xaxis_title="Potential / V vs Ref",
        yaxis_title=yaxis_title,
        legend=dict(orientation="v"),
        height=720,
    )

    return fig