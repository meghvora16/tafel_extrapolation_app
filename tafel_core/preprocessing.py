import numpy as np
import pandas as pd

from .config import TafelConfig
from .math_utils import safe_log10_abs, smooth_series


def resolve_scan_direction(raw_E, scan_mode="auto"):
    if scan_mode == "anodic":
        return 1

    if scan_mode == "cathodic":
        return -1

    return 1 if float(raw_E[-1]) > float(raw_E[0]) else -1


def prepare_dataframe(df: pd.DataFrame, config: TafelConfig):
    if config.potential_col not in df.columns:
        raise ValueError(f"Missing potential column: {config.potential_col}")

    if config.current_col not in df.columns:
        raise ValueError(f"Missing current column: {config.current_col}")

    raw_E = df[config.potential_col].dropna().to_numpy(dtype=float)
    scan_dir = resolve_scan_direction(raw_E, config.scan_mode)

    data = (
        df[[config.potential_col, config.current_col]]
        .rename(
            columns={
                config.potential_col: "E",
                config.current_col: "I",
            }
        )
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    data = data.sort_values("E").reset_index(drop=True)

    E = data["E"].to_numpy(dtype=float)
    I = data["I"].to_numpy(dtype=float)

    if len(E) < 20:
        raise ValueError("At least 20 valid data points are required.")

    if config.area_cm2 is not None and config.area_cm2 > 0:
        Y = np.abs(I) / config.area_cm2
        current_unit = "A cm^-2"
    else:
        Y = np.abs(I)
        current_unit = "A"

    ylog = safe_log10_abs(Y)

    if config.smoothing_enabled:
        window = max(
            11,
            int(len(ylog) * config.smoothing_window_fraction) | 1,
        )
        ylog_s = smooth_series(
            ylog,
            window=window,
            polyorder=config.smoothing_polyorder,
        )
    else:
        ylog_s = ylog.copy()

    dy_dE = np.gradient(ylog_s, E)
    d2y_dE2 = np.gradient(dy_dE, E)

    processed = pd.DataFrame(
        {
            "E_V": E,
            "I_A": I,
            "abs_current_or_density": Y,
            "log10_abs": ylog,
            "log10_abs_smooth": ylog_s,
            "dlog_dE": dy_dE,
            "d2log_dE2": d2y_dE2,
        }
    )

    return {
        "E": E,
        "I": I,
        "Y": Y,
        "ylog": ylog,
        "ylog_s": ylog_s,
        "dy_dE": dy_dE,
        "d2y_dE2": d2y_dE2,
        "scan_dir": scan_dir,
        "current_unit": current_unit,
        "processed": processed,
    }