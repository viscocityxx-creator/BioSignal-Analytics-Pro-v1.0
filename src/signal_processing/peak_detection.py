
import numpy as np
from scipy.signal import find_peaks

def detect_r_peaks(signal, fs, min_distance_seconds=0.45, prominence_factor=0.55):
    signal = np.asarray(signal, dtype=float)

    baseline = np.median(signal)
    centered = signal - baseline
    scale = np.std(centered)

    distance = max(1, int(min_distance_seconds * fs))
    prominence = max(1e-6, prominence_factor * scale)

    peaks, properties = find_peaks(
        centered,
        distance=distance,
        prominence=prominence
    )
    return peaks, properties
