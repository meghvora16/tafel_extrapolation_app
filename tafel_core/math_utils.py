import numpy as np
from scipy.signal import savgol_filter


def safe_log10_abs(y, floor=1e-30):
    return np.log10(np.maximum(np.abs(y), floor))


def r2_score(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot <= 0:
        return np.nan

    return 1.0 - np.sum((y_true - y_pred) ** 2) / ss_tot


def rmse(y_true, y_pred):
    return np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2))


def smooth_series(y, window=None, polyorder=3):
    y = np.asarray(y, dtype=float)
    n = len(y)

    if n < 7:
        return y.copy()

    if window is None:
        window = max(11, (n // 15) | 1)

    while window >= n:
        window -= 2

    if window < 5:
        window = 5

    if window % 2 == 0:
        window += 1

    polyorder = min(polyorder, window - 2)

    return savgol_filter(
        y,
        window_length=window,
        polyorder=polyorder,
        mode="interp",
    )


def logistic(x, x0, k):
    k = np.maximum(k, 1e-9)
    return 1.0 / (1.0 + np.exp(np.clip(-(x - x0) / k, -700, 700)))


def logistic_left(x, x0, k):
    k = np.maximum(k, 1e-9)
    return 1.0 / (1.0 + np.exp(np.clip((x - x0) / k, -700, 700)))


def softplus(x, s=0.02):
    s = max(float(s), 1e-9)
    return s * np.log1p(np.exp(np.clip(x / s, -700, 700)))


def softplus_left(x, s=0.02):
    s = max(float(s), 1e-9)
    return s * np.log1p(np.exp(np.clip(-x / s, -700, 700)))


def gaussian(x, mu, sigma):
    sigma = max(float(sigma), 1e-9)
    return np.exp(
        -0.5 * ((np.asarray(x, dtype=float) - mu) / sigma) ** 2
    )


def linear_fit(x, y):
    m, b = np.polyfit(x, y, 1)
    y_pred = m * x + b
    return {
        "slope": float(m),
        "intercept": float(b),
        "r2": float(r2_score(y, y_pred)),
        "rmse": float(rmse(y, y_pred)),
    }