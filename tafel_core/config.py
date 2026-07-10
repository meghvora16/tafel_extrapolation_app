from dataclasses import dataclass
from typing import Optional, Literal


ScanMode = Literal["auto", "anodic", "cathodic"]
ProcessingMode = Literal["single_upload", "multi_upload", "batch_folder"]
FitStrategy = Literal["classical", "global", "hybrid"]


@dataclass
class TafelConfig:
    # Data
    potential_col: str = "WE(1).Potential (V)"
    current_col: str = "WE(1).Current (A)"
    area_cm2: Optional[float] = None

    # Modes
    scan_mode: ScanMode = "auto"
    fit_strategy: FitStrategy = "hybrid"

    # Tafel manual windows, relative to Ecorr
    tafel_anodic_min_v: float = 0.015
    tafel_anodic_max_v: float = 0.028
    tafel_cathodic_min_v: float = 0.015
    tafel_cathodic_max_v: float = 0.045

    # Automatic Tafel search
    auto_tafel_enabled: bool = True
    auto_tafel_min_points: int = 5
    auto_tafel_min_width_v: float = 0.015
    auto_tafel_max_width_v: float = 0.120
    auto_tafel_r2_threshold: float = 0.985

    # Tafel slope physical bounds
    ba_min_v_dec: float = 0.030
    ba_max_v_dec: float = 0.300
    bc_min_v_dec: float = 0.030
    bc_max_v_dec: float = 0.450

    # Active fitting windows
    active_cathodic_v: float = 0.30
    active_anodic_v: float = 0.10

    # Smoothing
    smoothing_enabled: bool = True
    smoothing_window_fraction: float = 1 / 15
    smoothing_polyorder: int = 3

    # Global model regularization
    lambda_active: float = 0.06
    lambda_local: float = 0.08
    max_nfev: int = 140000

    # Passive / transpassive
    passive_detection_enabled: bool = True
    transpassive_detection_enabled: bool = True
    transpassive_guess_v: Optional[float] = None

    # Plotting
    dark_theme: bool = True
    dense_points: int = 1400

    # Batch
    target_filename: str = "lsv.xlsx"
    folder_keyword: Optional[str] = None