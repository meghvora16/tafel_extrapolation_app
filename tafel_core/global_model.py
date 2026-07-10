import numpy as np

from .math_utils import (
    logistic,
    logistic_left,
    softplus,
    softplus_left,
    gaussian,
    safe_log10_abs,
)


def polarization_global_model(
    Eq,
    pars,
    Ecorr0,
    icorr0,
    scan_dir,
):
    Eq = np.asarray(Eq, dtype=float)

    (
        Ec_shift,
        log_ic_shift,
        ba,
        bc,
        aloc,
        Eloc_shift,
        wloc,
        Epass,
        kpass,
        ypass,
        mpass,
        cpass,
        Etr,
        ktr,
        atr,
        mtr,
    ) = pars

    Ec = Ecorr0 + Ec_shift
    ic = icorr0 * (10 ** log_ic_shift)

    ba = max(ba, 1e-4)
    bc = max(bc, 1e-4)

    eta = Eq - Ec

    Iact = ic * (
        10 ** (eta / ba)
        - 10 ** (-eta / bc)
    )

    y_active = safe_log10_abs(Iact)

    y_active = y_active + aloc * gaussian(
        Eq,
        Ec + Eloc_shift,
        wloc,
    )

    if scan_dir == 1:
        S_pass = logistic(Eq, Epass, kpass)
        S_tr = logistic(Eq, Etr, ktr)

        dEpass = Eq - Epass

        y_pass = ypass + mpass * dEpass + cpass * dEpass ** 2

        y_trans = y_pass + atr * S_tr + mtr * softplus(
            Eq - Etr,
            s=max(ktr, 0.01),
        )

    else:
        S_pass = logistic_left(Eq, Epass, kpass)
        S_tr = logistic_left(Eq, Etr, ktr)

        dEpass = Epass - Eq

        y_pass = ypass + mpass * dEpass + cpass * dEpass ** 2

        y_trans = y_pass + atr * S_tr + mtr * softplus_left(
            Eq - Etr,
            s=max(ktr, 0.01),
        )

    y_stage12 = (1.0 - S_pass) * y_active + S_pass * y_pass

    y_final = (1.0 - S_tr) * y_stage12 + S_tr * y_trans

    return y_final


def build_auto_weights(E_all, Ec_local, Epass_est, Etr_est, scan_dir=1):
    weights = np.ones_like(E_all)

    if scan_dir == 1:
        cath_near = (E_all < Ec_local) & (E_all > Ec_local - 0.14)
        cath_far = E_all <= Ec_local - 0.14

        weights[cath_near] = 1.7
        weights[cath_far] = 1.1

        anodic_prepass = (
            (E_all > Ec_local + 0.03)
            & (E_all < Epass_est + 0.04)
        )
        weights[anodic_prepass] = np.maximum(
            weights[anodic_prepass],
            1.8,
        )

        shoulder = (
            (E_all >= Epass_est - 0.01)
            & (E_all < min(Epass_est + 0.10, Etr_est))
        )
        weights[shoulder] = np.maximum(weights[shoulder], 1.7)

        passive_plateau = (
            (E_all >= Epass_est + 0.10)
            & (E_all < Etr_est)
        )
        weights[passive_plateau] = np.maximum(
            weights[passive_plateau],
            1.05,
        )

        weights[E_all >= Etr_est] = np.maximum(
            weights[E_all >= Etr_est],
            1.15,
        )

    else:
        anod_near = (E_all > Ec_local) & (E_all < Ec_local + 0.14)
        anod_far = E_all >= Ec_local + 0.14

        weights[anod_near] = 1.7
        weights[anod_far] = 1.1

        cathodic_prepass = (
            (E_all < Ec_local - 0.03)
            & (E_all > Epass_est - 0.04)
        )
        weights[cathodic_prepass] = np.maximum(
            weights[cathodic_prepass],
            1.8,
        )

        shoulder = (
            (E_all <= Epass_est + 0.01)
            & (E_all > max(Epass_est - 0.10, Etr_est))
        )
        weights[shoulder] = np.maximum(weights[shoulder], 1.7)

        passive_plateau = (
            (E_all <= Epass_est - 0.10)
            & (E_all > Etr_est)
        )
        weights[passive_plateau] = np.maximum(
            weights[passive_plateau],
            1.05,
        )

        weights[E_all <= Etr_est] = np.maximum(
            weights[E_all <= Etr_est],
            1.15,
        )

    return weights