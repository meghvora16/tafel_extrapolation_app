from dataclasses import asdict
import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from .config import TafelConfig
from .preprocessing import prepare_dataframe
from .detection import (
    find_ecorr_robust,
    get_asymmetric_active_window,
    detect_passive_regions,
    has_transpassive_onset,
)
from .classical_tafel import (
    automatic_tafel_window_search,
    manual_tafel_fit,
)
from .global_model import (
    polarization_global_model,
    build_auto_weights,
)
from .math_utils import r2_score, rmse, safe_log10_abs


class TafelFitResult:
    def __init__(
        self,
        summary,
        processed_df,
        dense_df,
        diagnostics,
        arrays,
    ):
        self.summary = summary
        self.processed_df = processed_df
        self.dense_df = dense_df
        self.diagnostics = diagnostics
        self.arrays = arrays


def estimate_initial_tafel(E, I, Ecorr, scan_dir, config):
    ylog = safe_log10_abs(I)

    if scan_dir == -1:
        idx = int(np.argmin(ylog))
        Ec = float(E[idx])
        ic = float(max(abs(I[idx]), 1e-14))
    else:
        Ec = float(Ecorr)
        ic = float(max(np.min(np.abs(I)), 1e-14))

    ba = 0.080
    bc = 0.120

    cath_mask = (
        (E < Ecorr - 0.04)
        & (E > Ecorr - config.active_cathodic_v)
    )

    if np.sum(cath_mask) >= 5:
        s, _ = np.polyfit(E[cath_mask], ylog[cath_mask], 1)

        if s < -0.5:
            bc = float(
                np.clip(
                    abs(1.0 / s),
                    config.bc_min_v_dec,
                    config.bc_max_v_dec,
                )
            )

    anod_mask = (
        (E > Ecorr + 0.005)
        & (E < Ecorr + config.active_anodic_v)
    )

    if np.sum(anod_mask) >= 5:
        s, _ = np.polyfit(E[anod_mask], ylog[anod_mask], 1)

        if s > 0.5:
            ba = float(
                np.clip(
                    1.0 / s,
                    config.ba_min_v_dec,
                    config.ba_max_v_dec,
                )
            )

    return Ec, ic, ba, bc


class TafelFitter:
    def __init__(self, config: TafelConfig):
        self.config = config

    def fit_dataframe(self, df: pd.DataFrame, file_name="uploaded_file"):
        config = self.config

        prep = prepare_dataframe(df, config)

        E = prep["E"]
        I = prep["I"]
        ylog = prep["ylog"]
        dy_dE = prep["dy_dE"]
        d2y_dE2 = prep["d2y_dE2"]
        scan_dir = prep["scan_dir"]
        current_unit = prep["current_unit"]

        Ecorr_obs, ecorr_method = find_ecorr_robust(E, I, scan_dir)

        anodic_w, cathodic_w, passive_dominated = get_asymmetric_active_window(
            E,
            I,
            Ecorr_obs,
            scan_dir,
        )

        Ecorr0, icorr0, ba0, bc0 = estimate_initial_tafel(
            E,
            I,
            Ecorr_obs,
            scan_dir,
            config,
        )

        if config.passive_detection_enabled:
            Epass_auto, Etr_auto = detect_passive_regions(
                E,
                Ecorr0,
                dy_dE,
                d2y_dE2,
                scan_dir=scan_dir,
            )

            transpassive_exists = has_transpassive_onset(
                E,
                ylog,
                dy_dE,
                Epass_auto,
                Etr_auto,
                scan_dir=scan_dir,
            )

        else:
            Epass_auto = Ecorr0 + scan_dir * 0.12
            Etr_auto = Ecorr0 + scan_dir * 0.45
            transpassive_exists = False

        if scan_dir == 1:
            pass_mask = (
                (E > Epass_auto)
                & (E < min(Etr_auto, Epass_auto + 0.25))
            )
            ylog_side = ylog[E > Ecorr0]
        else:
            pass_mask = (
                (E < Epass_auto)
                & (E > max(Etr_auto, Epass_auto - 0.25))
            )
            ylog_side = ylog[E < Ecorr0]

        if np.sum(pass_mask) >= 5:
            ypass0 = float(np.median(ylog[pass_mask]))
        elif len(ylog_side) > 10:
            ypass0 = float(np.median(ylog_side))
        else:
            ypass0 = float(np.median(ylog))

        if scan_dir == 1:
            Epass0 = float(np.clip(Epass_auto, Ecorr0 + 0.05, E.max() - 0.12))

            if config.transpassive_guess_v is not None:
                Etr_initial = config.transpassive_guess_v
            else:
                Etr_initial = Etr_auto

            Etr0 = float(np.clip(Etr_initial, Epass0 + 0.10, E.max()))

        else:
            Epass0 = float(np.clip(Epass_auto, E.min() + 0.12, Ecorr0 - 0.05))

            if config.transpassive_guess_v is not None:
                Etr_initial = config.transpassive_guess_v
            else:
                Etr_initial = Etr_auto

            Etr0 = float(np.clip(Etr_initial, E.min(), Epass0 - 0.10))

        p0 = np.array(
            [
                0.0,
                0.0,
                ba0,
                bc0,
                0.0,
                -0.015,
                0.03,
                Epass0,
                0.03,
                ypass0,
                0.08,
                0.0,
                Etr0,
                0.06,
                0.15,
                1.0,
            ],
            dtype=float,
        )

        if scan_dir == 1:
            lb = np.array(
                [
                    -0.08,
                    -3.0,
                    config.ba_min_v_dec,
                    config.bc_min_v_dec,
                    -1.0,
                    -0.08,
                    0.010,
                    Ecorr0 - 0.03,
                    0.008,
                    -12.0,
                    -2.0,
                    -8.0,
                    Epass0 + 0.08,
                    0.008,
                    -2.0,
                    -2.0,
                ],
                dtype=float,
            )

            ub = np.array(
                [
                    0.08,
                    3.0,
                    config.ba_max_v_dec,
                    config.bc_max_v_dec,
                    1.0,
                    0.05,
                    0.080,
                    E.max(),
                    0.090,
                    -2.0,
                    2.0,
                    8.0,
                    E.max() + 0.2,
                    0.22,
                    2.0,
                    5.0,
                ],
                dtype=float,
            )

        else:
            lb = np.array(
                [
                    -0.08,
                    -3.0,
                    config.ba_min_v_dec,
                    config.bc_min_v_dec,
                    -1.0,
                    -0.08,
                    0.010,
                    E.min(),
                    0.008,
                    -12.0,
                    -2.0,
                    -8.0,
                    E.min() - 0.2,
                    0.008,
                    -2.0,
                    -2.0,
                ],
                dtype=float,
            )

            ub = np.array(
                [
                    0.08,
                    3.0,
                    config.ba_max_v_dec,
                    config.bc_max_v_dec,
                    1.0,
                    0.05,
                    0.080,
                    Ecorr0 + 0.03,
                    0.090,
                    -2.0,
                    2.0,
                    8.0,
                    Epass0 - 0.08,
                    0.22,
                    2.0,
                    5.0,
                ],
                dtype=float,
            )

        p0 = np.clip(p0, lb, ub)

        def residuals_global(pars):
            y_pred = polarization_global_model(
                E,
                pars,
                Ecorr0=Ecorr0,
                icorr0=icorr0,
                scan_dir=scan_dir,
            )

            weights = build_auto_weights(
                E,
                Ecorr0 + pars[0],
                pars[7],
                pars[12],
                scan_dir=scan_dir,
            )

            res_data = weights * (y_pred - ylog)

            reg_active = np.array(
                [
                    pars[0] / 0.05,
                    pars[1] / 1.0,
                    (pars[2] - ba0) / 0.05,
                    (pars[3] - bc0) / 0.08,
                ]
            ) * config.lambda_active

            reg_local = np.array(
                [
                    pars[4] / 0.4,
                    pars[5] / 0.04,
                    (pars[6] - 0.03) / 0.03,
                ]
            ) * config.lambda_local

            return np.concatenate([res_data, reg_active, reg_local])

        run_global = config.fit_strategy in ["global", "hybrid"]

        if run_global:
            opt = least_squares(
                residuals_global,
                x0=p0,
                bounds=(lb, ub),
                max_nfev=config.max_nfev,
                verbose=0,
            )

            popt = opt.x

            yfit = polarization_global_model(
                E,
                popt,
                Ecorr0=Ecorr0,
                icorr0=icorr0,
                scan_dir=scan_dir,
            )

            R2 = r2_score(ylog, yfit)
            RMSE = rmse(ylog, yfit)

            (
                Ec_shift,
                log_ic_shift,
                ba_fit,
                bc_fit,
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
            ) = popt

            Ecorr_global = Ecorr0 + Ec_shift
            icorr_global = icorr0 * (10 ** log_ic_shift)

        else:
            opt = None
            popt = p0
            yfit = np.full_like(ylog, np.nan)
            R2 = np.nan
            RMSE = np.nan
            ba_fit = ba0
            bc_fit = bc0
            Ecorr_global = Ecorr0
            icorr_global = icorr0
            Epass = Epass0
            Etr = Etr0
            kpass = np.nan
            ktr = np.nan
            cpass = np.nan
            aloc = np.nan
            Eloc_shift = np.nan
            wloc = np.nan

        if config.fit_strategy == "classical":
            tafel_result = manual_tafel_fit(E, ylog, Ecorr_obs, config)

        elif config.auto_tafel_enabled:
            tafel_result = automatic_tafel_window_search(
                E,
                ylog,
                Ecorr_global,
                config,
            )

        else:
            tafel_result = manual_tafel_fit(
                E,
                ylog,
                Ecorr_global,
                config,
            )

        if tafel_result["tafel_ok"]:
            Ecorr_final = tafel_result["Ecorr_tafel_V"]
            Icorr_final = tafel_result["Icorr_tafel_abs"]
            ba_final = tafel_result["ba_V_dec"]
            bc_final = tafel_result["bc_V_dec"]
            result_source = "tafel_intersection"
        else:
            Ecorr_final = Ecorr_global
            Icorr_final = icorr_global
            ba_final = ba_fit
            bc_final = bc_fit
            result_source = "global_fallback"

        E_dense = np.linspace(E.min(), E.max(), config.dense_points)

        if run_global:
            y_dense = polarization_global_model(
                E_dense,
                popt,
                Ecorr0=Ecorr0,
                icorr0=icorr0,
                scan_dir=scan_dir,
            )
        else:
            y_dense = np.full_like(E_dense, np.nan)

        dense_df = pd.DataFrame(
            {
                "E_V": E_dense,
                "log10_abs_fit": y_dense,
            }
        )

        if config.area_cm2 is not None and config.area_cm2 > 0:
            dense_df["abs_fit_A_cm2"] = 10 ** y_dense
        else:
            dense_df["abs_fit_A"] = 10 ** y_dense

        processed_df = prep["processed"].copy()
        processed_df["log10_fit"] = yfit
        processed_df["residual_log"] = yfit - ylog

        scan_label = "Anodic" if scan_dir == 1 else "Cathodic"

        summary = {
            "file_name": file_name,
            "scan_direction": scan_label,
            "fit_strategy": config.fit_strategy,
            "result_source": result_source,
            "Ecorr_observed_V": float(Ecorr_obs),
            "Ecorr_detection_method": ecorr_method,
            "Ecorr_global_V": float(Ecorr_global),
            "Ecorr_final_V": float(Ecorr_final),
            "Icorr_abs": float(Icorr_final),
            "current_unit": current_unit,
            "ba_V_dec": float(ba_final),
            "bc_V_dec": float(bc_final),
            "ba_initial_guess": float(ba0),
            "bc_initial_guess": float(bc0),
            "passive_dominated": bool(passive_dominated),
            "Epp_V": float(Epass),
            "transpassive_detected": bool(transpassive_exists),
            "Eb_V": float(Etr) if transpassive_exists else None,
            "R2_log_global": float(R2),
            "RMSE_log_global": float(RMSE),
            "tafel_ok": bool(tafel_result["tafel_ok"]),
            "tafel_reason": tafel_result["reason"],
            "tafel_auto_window_used": bool(
                tafel_result.get("auto_window_used", False)
            ),
            "kpass_V": float(kpass) if np.isfinite(kpass) else None,
            "ktrans_V": float(ktr) if np.isfinite(ktr) else None,
            "cpass": float(cpass) if np.isfinite(cpass) else None,
            "local_corr_amplitude": float(aloc) if np.isfinite(aloc) else None,
            "local_corr_shift_V": (
                float(Eloc_shift) if np.isfinite(Eloc_shift) else None
            ),
            "local_corr_width_V": (
                float(wloc) if np.isfinite(wloc) else None
            ),
        }

        diagnostics = {
            "optimizer_success": bool(opt.success) if opt is not None else None,
            "optimizer_message": opt.message if opt is not None else None,
            "optimizer_cost": float(opt.cost) if opt is not None else None,
            "optimizer_nfev": int(opt.nfev) if opt is not None else None,
            "parameters": popt.tolist(),
            "config": asdict(config),
            "tafel_result": tafel_result,
        }

        arrays = {
            "E": E,
            "I": I,
            "ylog": ylog,
            "yfit": yfit,
            "E_dense": E_dense,
            "y_dense": y_dense,
            "scan_dir": scan_dir,
            "Ecorr_obs": Ecorr_obs,
            "Ecorr_final": Ecorr_final,
            "Icorr_final": Icorr_final,
            "Epass": Epass,
            "Etr": Etr,
            "transpassive_exists": transpassive_exists,
            "tafel_result": tafel_result,
        }

        return TafelFitResult(
            summary=summary,
            processed_df=processed_df,
            dense_df=dense_df,
            diagnostics=diagnostics,
            arrays=arrays,
        )