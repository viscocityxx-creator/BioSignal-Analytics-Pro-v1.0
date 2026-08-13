
import numpy as np

def rr_intervals_from_peak_times(peak_times):
    peak_times = np.asarray(peak_times, dtype=float)
    if len(peak_times) < 2:
        return np.array([], dtype=float)
    return np.diff(peak_times)

def bpm_from_rr(rr_intervals):
    rr_intervals = np.asarray(rr_intervals, dtype=float)
    rr_intervals = rr_intervals[rr_intervals > 0]
    if len(rr_intervals) == 0:
        return np.array([], dtype=float)
    return 60.0 / rr_intervals

def hrv_metrics(rr_intervals):
    rr = np.asarray(rr_intervals, dtype=float)
    if len(rr) < 2:
        return {
            "mean_rr_s": float(rr.mean()) if len(rr) else None,
            "sdnn_ms": None,
            "rmssd_ms": None,
        }

    mean_rr = float(np.mean(rr))
    sdnn_ms = float(np.std(rr, ddof=1) * 1000)
    successive = np.diff(rr)
    rmssd_ms = float(np.sqrt(np.mean(successive ** 2)) * 1000) if len(successive) else None

    return {
        "mean_rr_s": mean_rr,
        "sdnn_ms": sdnn_ms,
        "rmssd_ms": rmssd_ms,
    }
