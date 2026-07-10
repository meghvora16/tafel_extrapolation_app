import numpy as np


def generate_quality_flags(summary):
    flags = []

    if not summary.get("tafel_ok", False):
        flags.append(
            {
                "level": "warning",
                "message": "Tafel-line intersection was not reliable. Global fallback was used.",
            }
        )

    if summary.get("passive_dominated", False):
        flags.append(
            {
                "level": "warning",
                "message": "Curve is passive-dominated. Interpret anodic slope carefully.",
            }
        )

    r2 = summary.get("R2_log_global", np.nan)

    if np.isfinite(r2) and r2 < 0.95:
        flags.append(
            {
                "level": "warning",
                "message": f"Global logarithmic fit quality is low: R²={r2:.4f}.",
            }
        )

    ba = summary.get("ba_V_dec", np.nan)
    bc = summary.get("bc_V_dec", np.nan)

    if np.isfinite(ba) and not (0.03 <= ba <= 0.30):
        flags.append(
            {
                "level": "warning",
                "message": f"Anodic slope ba={ba:.4f} V/dec is outside typical bounds.",
            }
        )

    if np.isfinite(bc) and not (0.03 <= bc <= 0.45):
        flags.append(
            {
                "level": "warning",
                "message": f"Cathodic slope bc={bc:.4f} V/dec is outside typical bounds.",
            }
        )

    if summary.get("Icorr_abs", 0) <= 0:
        flags.append(
            {
                "level": "error",
                "message": "Computed Icorr is non-positive.",
            }
        )

    if not flags:
        flags.append(
            {
                "level": "success",
                "message": "No major quality issues detected.",
            }
        )

    return flags