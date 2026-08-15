import numpy as np


def signal_quality_summary(raw_signal, filtered_signal, bpm_values, rr_intervals, missing_fraction=0.0):
    raw = np.asarray(raw_signal, dtype=float)
    filt = np.asarray(filtered_signal, dtype=float)
    bpm = np.asarray(bpm_values, dtype=float)
    rr = np.asarray(rr_intervals, dtype=float)

    raw_std = float(np.std(raw)) if len(raw) else 0.0
    filtered_std = float(np.std(filt)) if len(filt) else 0.0
    residual = raw - filt if len(raw) == len(filt) else np.array([])
    residual_std = float(np.std(residual)) if len(residual) else None

    score = 100.0
    issues = []

    if missing_fraction > 0:
        score -= min(35.0, missing_fraction * 1000)
        if missing_fraction > 0.01:
            issues.append("More than 1% of input samples were missing or non-numeric")

    if len(bpm) == 0:
        score -= 55
        issues.append("No valid beat-to-beat heart-rate intervals were detected")

    if len(rr) >= 3:
        rr_cv = float(np.std(rr) / np.mean(rr)) if np.mean(rr) > 0 else None
        if rr_cv is not None and rr_cv > 0.35:
            score -= min(25.0, (rr_cv - 0.35) * 50)
            issues.append("Large R-R variability detected; review rhythm and peak detections")
    else:
        rr_cv = None

    # Signal-to-residual ratio is a heuristic engineering quality indicator, not a clinical metric.
    if residual_std is not None and residual_std > 0:
        snr_proxy_db = float(20 * np.log10((filtered_std + 1e-12) / (residual_std + 1e-12)))
        if snr_proxy_db < -6:
            score -= 20
            issues.append("High residual noise relative to filtered signal")
    else:
        snr_proxy_db = None

    score = float(np.clip(score, 0, 100))
    if score >= 85:
        rating = "Good"
    elif score >= 65:
        rating = "Acceptable"
    else:
        rating = "Needs Review"

    return {
        "rating": rating,
        "score": score,
        "missing_fraction": float(missing_fraction),
        "raw_std": raw_std,
        "filtered_std": filtered_std,
        "residual_std": residual_std,
        "snr_proxy_db": snr_proxy_db,
        "rr_coefficient_of_variation": rr_cv,
        "issues": issues,
        "note": "Quality metrics are engineering heuristics and are not clinically validated.",
    }
