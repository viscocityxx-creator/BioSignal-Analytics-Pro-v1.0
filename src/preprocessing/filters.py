
import numpy as np
from scipy.signal import butter, filtfilt

def moving_average(signal, window=7):
    signal = np.asarray(signal, dtype=float)
    if window < 1:
        raise ValueError("window must be >= 1")
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(signal, kernel, mode="same")

def bandpass_filter(signal, fs, lowcut=0.5, highcut=18.0, order=4):
    signal = np.asarray(signal, dtype=float)
    nyquist = fs / 2.0
    if lowcut <= 0 or highcut >= nyquist or lowcut >= highcut:
        raise ValueError("Invalid bandpass cutoff frequencies.")
    b, a = butter(order, [lowcut / nyquist, highcut / nyquist], btype="band")
    return filtfilt(b, a, signal)
