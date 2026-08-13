
import numpy as np
from src.signal_processing.hrv import rr_intervals_from_peak_times, bpm_from_rr

def test_rr_and_bpm():
    peak_times = np.array([0.0, 1.0, 2.0, 3.0])
    rr = rr_intervals_from_peak_times(peak_times)
    bpm = bpm_from_rr(rr)
    assert np.allclose(rr, [1.0, 1.0, 1.0])
    assert np.allclose(bpm, [60.0, 60.0, 60.0])
