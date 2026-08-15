import numpy as np
from scipy.signal import butter, filtfilt, detrend


def moving_average(signal, window=7):
    signal = np.asarray(signal, dtype=float)
    if window < 1:
        raise ValueError("window must be >= 1")
    window = min(int(window), max(1, len(signal)))
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(signal, kernel, mode="same")


def adaptive_bandpass_filter(signal, fs, order=4):
    """ECG-oriented filter whose upper cutoff adapts to the recording's Nyquist limit."""
    signal = np.asarray(signal, dtype=float)
    if fs <= 2:
        raise ValueError("Sampling frequency is too low for ECG filtering.")

    nyquist = fs / 2.0
    lowcut = 0.5
    highcut = min(35.0, nyquist * 0.80)

    if highcut <= lowcut:
        # Very low-rate data: remove linear trend but avoid an invalid digital filter.
        return detrend(signal), {"lowcut_hz": None, "highcut_hz": None, "mode": "detrend"}

    b, a = butter(order, [lowcut / nyquist, highcut / nyquist], btype="band")
    filtered = filtfilt(b, a, signal)
    return filtered, {"lowcut_hz": lowcut, "highcut_hz": highcut, "mode": "bandpass"}


def adaptive_smoothing_window(fs):
    """Choose a short smoothing window from the sampling rate (about 20 ms)."""
    return max(1, int(round(0.020 * fs)))
