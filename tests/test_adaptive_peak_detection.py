import numpy as np
from src.signal_processing.peak_detection import detect_r_peaks


def synthetic_ecg(fs=250, duration=12, bpm=72, inverted=False, noise=0.02):
    rng = np.random.default_rng(123)
    t = np.arange(0, duration, 1/fs)
    rr = 60 / bpm
    beat_times = np.arange(0.7, duration - 0.2, rr)
    x = 0.03 * np.sin(2*np.pi*0.2*t)
    for bt in beat_times:
        r = np.exp(-((t-bt)/0.014)**2)
        q = -0.10*np.exp(-((t-(bt-0.025))/0.012)**2)
        s = -0.20*np.exp(-((t-(bt+0.028))/0.014)**2)
        p = 0.08*np.exp(-((t-(bt-0.18))/0.035)**2)
        tw = 0.24*np.exp(-((t-(bt+0.26))/0.065)**2)
        x += p + q + r + s + tw
    if inverted:
        x = -x
    x += rng.normal(0, noise, len(t))
    return t, x, beat_times


def _assert_detection(bpm, inverted=False):
    fs = 250
    t, signal, truth = synthetic_ecg(fs=fs, bpm=bpm, inverted=inverted)
    peaks, meta = detect_r_peaks(signal, fs)
    detected = t[peaks]
    # Require near-correct beat count and median timing error below 50 ms.
    assert abs(len(detected) - len(truth)) <= 1
    errors = []
    for expected in truth:
        errors.append(np.min(np.abs(detected - expected)))
    assert np.median(errors) < 0.05
    assert meta["method"] == "adaptive_energy_autocorrelation"


def test_adaptive_detector_slow_normal_fast_and_inverted():
    for bpm in (48, 72, 120):
        _assert_detection(bpm)
    _assert_detection(72, inverted=True)
