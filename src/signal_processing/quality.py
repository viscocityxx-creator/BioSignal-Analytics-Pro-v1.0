
import numpy as np

def signal_quality_summary(raw_signal, filtered_signal, bpm_values, missing_fraction=0.0):
    raw = np.asarray(raw_signal, dtype=float)
    filt = np.asarray(filtered_signal, dtype=float)
    bpm = np.asarray(bpm_values, dtype=float)

    raw_std = float(np.std(raw))
    filtered_std = float(np.std(filt))
    noise_reduction_ratio = None
    if raw_std > 0:
        noise_reduction_ratio = float(1.0 - filtered_std/raw_std)

    issues = []
    if missing_fraction > 0.01:
        issues.append("Too many missing samples")
    if len(bpm) == 0:
        issues.append("No valid heart-rate intervals detected")
    elif np.any((bpm < 35) | (bpm > 220)):
        issues.append("Implausible instantaneous BPM detected")

    if issues:
        rating = "Needs Review"
    elif noise_reduction_ratio is not None and noise_reduction_ratio > 0.75:
        rating = "Over-smoothed"
    else:
        rating = "Acceptable"

    return {
        "rating": rating,
        "missing_fraction": float(missing_fraction),
        "raw_std": raw_std,
        "filtered_std": filtered_std,
        "noise_reduction_ratio": noise_reduction_ratio,
        "issues": issues,
    }
