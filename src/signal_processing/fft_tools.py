
import numpy as np

def frequency_spectrum(signal, fs):
    signal = np.asarray(signal, dtype=float)
    centered = signal - np.mean(signal)
    n = len(centered)
    frequencies = np.fft.rfftfreq(n, d=1.0/fs)
    magnitude = np.abs(np.fft.rfft(centered)) / max(n, 1)
    return frequencies, magnitude

def dominant_frequency(signal, fs, min_hz=0.1, max_hz=40.0):
    frequencies, magnitude = frequency_spectrum(signal, fs)
    mask = (frequencies >= min_hz) & (frequencies <= max_hz)
    if not mask.any():
        return None
    idx_local = np.argmax(magnitude[mask])
    return float(frequencies[mask][idx_local])
