import numpy as np

from .math_utils import safe_log10_abs, linear_fit


def fit_line_in_window(E, ylog, mask):
    if np.sum(mask) < 3:
        return None

    x = E[mask]
    y = ylog[mask]

    fit = linear_fit(x, y)
    fit["n_points"] = int(len(x))
    fit["E_min"] = float(x.min())
    fit["E_max"] = float(x.max())

    return fit


def manual_tafel_fit(E, ylog, Ecorr, config):
    anodic_mask = (
        (E > Ecorr + config.tafel_anodic_min_v)
        & (E < Ecorr + config.tafel_anodic_max_v)
    )

    cathodic_mask = (
        (E < Ecorr - config.tafel_cathodic_min_v)
        & (E > Ecorr - config.tafel_cathodic_max_v)
    )

    anodic_fit = fit_line_in_window(E, ylog, anodic_mask)
    cathodic_fit = fit_line_in_window(E, ylog, cathodic_mask)

    return compute_tafel_intersection(
        anodic_fit,
        cathodic_fit,
        Ecorr_fallback=Ecorr,
    )


def compute_tafel_intersection(anodic_fit, cathodic_fit, Ecorr_fallback):
    if anodic_fit is None or cathodic_fit is None:
        return {
            "tafel_ok": False,
            "reason": "not_enough_points",
            "Ecorr_tafel_V": float(Ecorr_fallback),
            "Icorr_tafel_abs": np.nan,
            "log_Icorr": np.nan,
            "anodic_fit": anodic_fit,
            "cathodic_fit": cathodic_fit,
            "ba_V_dec": np.nan,
            "bc_V_dec": np.nan,
        }

    m_an = anodic_fit["slope"]
    b_an = anodic_fit["intercept"]

    m_ca = cathodic_fit["slope"]
    b_ca = cathodic_fit["intercept"]

    if abs(m_an - m_ca) < 1e-12:
        return {
            "tafel_ok": False,
            "reason": "parallel_lines",
            "Ecorr_tafel_V": float(Ecorr_fallback),
            "Icorr_tafel_abs": np.nan,
            "log_Icorr": np.nan,
            "anodic_fit": anodic_fit,
            "cathodic_fit": cathodic_fit,
            "ba_V_dec": np.nan,
            "bc_V_dec": np.nan,
        }

    Ecross = (b_ca - b_an) / (m_an - m_ca)
    log_ic = m_an * Ecross + b_an
    icorr = 10 ** log_ic

    ba = 1.0 / m_an if m_an > 0 else np.nan
    bc = abs(1.0 / m_ca) if m_ca < 0 else np.nan

    return {
        "tafel_ok": True,
        "reason": "ok",
        "Ecorr_tafel_V": float(Ecross),
        "Icorr_tafel_abs": float(icorr),
        "log_Icorr": float(log_ic),
        "anodic_fit": anodic_fit,
        "cathodic_fit": cathodic_fit,
        "ba_V_dec": float(ba),
        "bc_V_dec": float(bc),
    }


def automatic_tafel_window_search(E, ylog, Ecorr, config):
    candidates_an = []
    candidates_ca = []

    min_pts = config.auto_tafel_min_points

    # anodic side
    anodic_indices = np.where(E > Ecorr + 0.005)[0]

    for i in range(len(anodic_indices)):
        for j in range(i + min_pts, len(anodic_indices)):
            idx = anodic_indices[i:j]
            width = E[idx[-1]] - E[idx[0]]

            if width < config.auto_tafel_min_width_v:
                continue

            if width > config.auto_tafel_max_width_v:
                break

            fit = linear_fit(E[idx], ylog[idx])

            slope = fit["slope"]
            ba = 1.0 / slope if slope > 0 else np.nan

            if (
                slope > 0
                and config.ba_min_v_dec <= ba <= config.ba_max_v_dec
            ):
                fit["E_min"] = float(E[idx[0]])
                fit["E_max"] = float(E[idx[-1]])
                fit["n_points"] = int(len(idx))
                fit["ba_V_dec"] = float(ba)
                candidates_an.append(fit)

    # cathodic side
    cathodic_indices = np.where(E < Ecorr - 0.005)[0]

    for i in range(len(cathodic_indices)):
        for j in range(i + min_pts, len(cathodic_indices)):
            idx = cathodic_indices[i:j]
            width = E[idx[-1]] - E[idx[0]]

            if width < config.auto_tafel_min_width_v:
                continue

            if width > config.auto_tafel_max_width_v:
                break

            fit = linear_fit(E[idx], ylog[idx])

            slope = fit["slope"]
            bc = abs(1.0 / slope) if slope < 0 else np.nan

            if (
                slope < 0
                and config.bc_min_v_dec <= bc <= config.bc_max_v_dec
            ):
                fit["E_min"] = float(E[idx[0]])
                fit["E_max"] = float(E[idx[-1]])
                fit["n_points"] = int(len(idx))
                fit["bc_V_dec"] = float(bc)
                candidates_ca.append(fit)

    if not candidates_an or not candidates_ca:
        return manual_tafel_fit(E, ylog, Ecorr, config)

    candidates_an = sorted(
        candidates_an,
        key=lambda d: (d["r2"], d["n_points"]),
        reverse=True,
    )

    candidates_ca = sorted(
        candidates_ca,
        key=lambda d: (d["r2"], d["n_points"]),
        reverse=True,
    )

    anodic_best = candidates_an[0]
    cathodic_best = candidates_ca[0]

    result = compute_tafel_intersection(
        anodic_best,
        cathodic_best,
        Ecorr_fallback=Ecorr,
    )

    result["auto_window_used"] = True
    result["anodic_candidates_count"] = len(candidates_an)
    result["cathodic_candidates_count"] = len(candidates_ca)

    return result