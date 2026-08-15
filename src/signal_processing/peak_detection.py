from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def _mad(x):
    x = np.asarray(x, dtype=float)
    med = np.median(x)
    return np.median(np.abs(x - med))


def _estimate_rr_from_autocorrelation(envelope, fs):
    """Estimate repeating beat period from the QRS-energy envelope.

    The search uses broad ECG-compatible lag guardrails, but the chosen R-R period
    comes from the recording itself rather than a configured BPM value.
    """
    x = np.asarray(envelope, dtype=float)
    x = x - np.mean(x)
    if len(x) < int(fs):
        return None

    corr = np.correlate(x, x, mode="full")[len(x)-1:]
    # Broad guardrails: 0.28-2.0 s. These limit nonsensical autocorrelation lags;
    # they are not used as a patient-specific heart-rate threshold.
    min_lag = max(1, int(0.28 * fs))
    max_lag = min(len(corr) - 1, int(2.0 * fs))
    if max_lag <= min_lag:
        return None

    segment = corr[min_lag:max_lag + 1]
    if not np.isfinite(segment).any() or np.max(segment) <= 0:
        return None
    lag = min_lag + int(np.argmax(segment))
    return lag / fs


def detect_r_peaks(signal, fs):
    """Adaptive R-peak detector using a Pan-Tompkins-inspired energy envelope.

    Adaptation strategy:
    1. Robustly center/scale the signal using median and MAD.
    2. Build a QRS-energy envelope from the squared derivative.
    3. Estimate R-R periodicity from envelope autocorrelation.
    4. Derive peak spacing from the estimated R-R interval.
    5. Derive prominence from the envelope's own robust distribution.
    6. Refine each candidate to the strongest local ECG deflection.
    """
    signal = np.asarray(signal, dtype=float)
    if len(signal) < 5:
        return np.array([], dtype=int), {"method": "adaptive", "reason": "signal_too_short"}

    median = float(np.median(signal))
    robust_sigma = 1.4826 * _mad(signal)
    if not np.isfinite(robust_sigma) or robust_sigma < 1e-9:
        robust_sigma = float(np.std(signal)) or 1.0

    z = (signal - median) / robust_sigma
    derivative = np.gradient(z)
    energy = derivative ** 2

    integration_window = max(1, int(round(0.080 * fs)))
    kernel = np.ones(integration_window) / integration_window
    envelope = np.convolve(energy, kernel, mode="same")

    rr_estimate = _estimate_rr_from_autocorrelation(envelope, fs)
    if rr_estimate is None:
        # Fallback based on candidate spacing from the data itself.
        rough, _ = find_peaks(envelope, prominence=max(_mad(envelope) * 2.0, 1e-9))
        if len(rough) >= 2:
            rr_estimate = float(np.median(np.diff(rough)) / fs)
        else:
            rr_estimate = 0.8

    min_distance_samples = max(1, int(round(0.55 * rr_estimate * fs)))

    env_median = float(np.median(envelope))
    env_mad = float(_mad(envelope))
    upper = float(np.percentile(envelope, 90))
    prominence = max(2.5 * env_mad, 0.20 * max(upper - env_median, 0.0), 1e-9)

    candidates, properties = find_peaks(
        envelope,
        distance=min_distance_samples,
        prominence=prominence,
    )

    # Refine envelope peaks to true ECG deflections. Using absolute amplitude also
    # supports inverted leads where R complexes point downward.
    half_window = max(1, int(round(0.10 * fs)))
    refined = []
    for candidate in candidates:
        left = max(0, candidate - half_window)
        right = min(len(signal), candidate + half_window + 1)
        local = np.abs(signal[left:right] - median)
        if len(local):
            refined.append(left + int(np.argmax(local)))

    if refined:
        refined = np.array(sorted(set(refined)), dtype=int)
        # Deduplicate after refinement using a data-derived spacing constraint.
        final = [int(refined[0])]
        for idx in refined[1:]:
            if idx - final[-1] >= min_distance_samples:
                final.append(int(idx))
            elif abs(signal[idx] - median) > abs(signal[final[-1]] - median):
                final[-1] = int(idx)
        peaks = np.asarray(final, dtype=int)
    else:
        peaks = np.array([], dtype=int)

    metadata = dict(properties)
    metadata.update({
        "method": "adaptive_energy_autocorrelation",
        "estimated_rr_s": float(rr_estimate),
        "derived_min_distance_samples": int(min_distance_samples),
        "derived_min_distance_s": float(min_distance_samples / fs),
        "derived_prominence": float(prominence),
        "robust_signal_sigma": float(robust_sigma),
        "integration_window_samples": int(integration_window),
        "candidate_count": int(len(candidates)),
    })
    return peaks, metadata
