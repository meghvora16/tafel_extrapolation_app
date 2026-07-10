import numpy as np

from .math_utils import safe_log10_abs


def find_ecorr_robust(E, I, scan_dir=1):
    ylog = safe_log10_abs(I)

    if scan_dir == -1:
        min_idx = int(np.argmin(ylog))
        return float(E[min_idx]), "passive_vdip_min"

    low_mask = E < 0.20

    if np.sum(low_mask) > 5:
        E_low = E[low_mask]
        I_low = I[low_mask]

        sign_changes = np.where(np.diff(np.sign(I_low)))[0]

        if len(sign_changes) > 0:
            s = sign_changes[-1]
            Ec = float(0.5 * (E_low[s] + E_low[s + 1]))
            return Ec, "sign_change"

    her_cutoff = min(-0.15, float(np.percentile(E, 30)))
    her_mask = E < her_cutoff
    pass_mask = (E > -0.10) & (E < 0.35)

    if np.sum(her_mask) >= 6 and np.sum(pass_mask) >= 5:
        log_I_her = safe_log10_abs(I[her_mask])
        slope, intercept = np.polyfit(E[her_mask], log_I_her, 1)

        if abs(slope) > 0.5:
            log_Ipass = safe_log10_abs(np.median(np.abs(I[pass_mask])))
            Ec = float(
                np.clip(
                    (log_Ipass - intercept) / slope,
                    float(E.min()),
                    0.25,
                )
            )
            return Ec, "HER_tafel"

    low_mask2 = E < 0.20

    if np.sum(low_mask2) > 3:
        return (
            float(E[low_mask2][np.argmin(np.abs(I[low_mask2]))]),
            "argmin_lowE",
        )

    return float(E[np.argmin(np.abs(I))]), "argmin_full"


def detect_immediate_passivation(E, I, Ecorr, scan_dir):
    if scan_dir == 1:
        near = (E > Ecorr + 0.01) & (E < Ecorr + 0.07)
        far = (E > Ecorr + 0.07) & (E < Ecorr + 0.20)
    else:
        near = (E < Ecorr - 0.01) & (E > Ecorr - 0.07)
        far = (E < Ecorr - 0.07) & (E > Ecorr - 0.20)

    if np.sum(near) < 3 or np.sum(far) < 3:
        return False

    I_near = np.median(np.abs(I[near]))
    I_far = np.median(np.abs(I[far]))

    return I_far < 2.5 * I_near


def get_asymmetric_active_window(E, I, Ecorr, scan_dir):
    if scan_dir == -1:
        return 0.45, 0.40, True

    passive_dominated = detect_immediate_passivation(E, I, Ecorr, scan_dir)

    anodic_w = 0.06 if passive_dominated else 0.14
    cathodic_w = 0.32

    return anodic_w, cathodic_w, passive_dominated


def detect_passive_regions(E, Ecorr, dy_dE, d2y_dE2, scan_dir=1):
    active_mask = E > Ecorr if scan_dir == 1 else E < Ecorr

    E_active = E[active_mask]
    dy_active = dy_dE[active_mask]

    if len(E_active) < 10:
        return (
            float(Ecorr + scan_dir * 0.08),
            float(Ecorr + scan_dir * 0.28),
        )

    if scan_dir == -1:
        E_active = E_active[::-1]
        dy_active = dy_active[::-1]

    offset = 0.03

    ref_mask = (
        (np.abs(E_active - Ecorr) > offset)
        & (np.abs(E_active - Ecorr) < offset + 0.07)
    )

    if np.sum(ref_mask) >= 4:
        slope_ref = float(np.median(dy_active[ref_mask]))
    else:
        slope_ref = float(np.max(dy_active[: min(len(dy_active), 8)]))

    search_mask = (
        (np.abs(E_active - Ecorr) > 0.05)
        & (np.abs(E_active - Ecorr) < 0.35)
    )

    if np.sum(search_mask) >= 5:
        E_s = E_active[search_mask]
        dy_s = dy_active[search_mask]
        candidates = np.where(dy_s < 0.65 * slope_ref)[0]

        if len(candidates) > 0:
            Epass = float(E_s[candidates[0]])
        else:
            Epass = float(Ecorr + scan_dir * 0.12)
    else:
        Epass = float(Ecorr + scan_dir * 0.12)

    search2 = np.abs(E_active - Ecorr) > (np.abs(Epass - Ecorr) + 0.10)

    if np.sum(search2) >= 5:
        E2 = E_active[search2]
        dy2 = dy_active[search2]

        if len(dy2) >= 3:
            slope_pass = float(np.median(dy2[: max(3, len(dy2) // 5)]))
        else:
            slope_pass = float(np.median(dy2))

        candidates2 = np.where(
            dy2 > max(slope_pass * 1.5, slope_pass + 0.15)
        )[0]

        if len(candidates2) > 0:
            Etr = float(E2[candidates2[0]])
        else:
            dist = np.abs(Epass - Ecorr) + 0.35
            Etr = float(
                Ecorr + scan_dir * min(dist, np.abs(E - Ecorr).max())
            )
    else:
        dist = np.abs(Epass - Ecorr) + 0.35
        Etr = float(
            Ecorr + scan_dir * min(dist, np.abs(E - Ecorr).max())
        )

    if scan_dir == 1:
        if Etr <= Epass + 0.08:
            Etr = Epass + 0.10

        Epass = float(np.clip(Epass, Ecorr + 0.05, E.max() - 0.12))
        Etr = float(np.clip(Etr, Epass + 0.10, E.max()))

    else:
        if Etr >= Epass - 0.08:
            Etr = Epass - 0.10

        Epass = float(np.clip(Epass, E.min() + 0.12, Ecorr - 0.05))
        Etr = float(np.clip(Etr, E.min(), Epass - 0.10))

    return Epass, Etr


def has_transpassive_onset(E, ylog, dy_dE, Epass, Etr_candidate, scan_dir=1):
    if scan_dir == 1:
        plateau_mask = (E > Epass + 0.05) & (E < Etr_candidate - 0.02)
        beyond_mask = E > Etr_candidate - 0.03
    else:
        plateau_mask = (E < Epass - 0.05) & (E > Etr_candidate + 0.02)
        beyond_mask = E < Etr_candidate + 0.03

    if np.sum(plateau_mask) < 4 or np.sum(beyond_mask) < 4:
        return False

    slope_plateau = float(np.median(np.abs(dy_dE[plateau_mask])))
    slope_beyond = float(np.median(np.abs(dy_dE[beyond_mask])))

    if slope_beyond < 2.0 * slope_plateau:
        return False

    ylog_plateau_end = float(np.median(ylog[plateau_mask][-3:]))
    ylog_beyond_start = float(np.median(ylog[beyond_mask][:3]))

    return ylog_beyond_start > ylog_plateau_end + 0.15