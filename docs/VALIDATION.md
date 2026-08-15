# v2.0 Synthetic Validation Summary

BioSignal Analytics Pro v2.0 was smoke-tested on ten synthetic ECG recordings generated with known beat times and nominal heart rates. The validation set intentionally varies sampling rate, noise, baseline wander, amplitude, rhythm regularity, signal inversion, input format, and column naming.

> This validation demonstrates software behavior on controlled synthetic data only. It is **not clinical validation**.

## Batch Result

- Supported files processed: **10**
- Successful analyses: **10**
- Failed analyses: **0**
- Exact expected beat-count matches: **10 / 10**
- Mean absolute error of average BPM vs. nominal generator BPM: **0.41 BPM**
- Maximum absolute average-BPM error in this synthetic set: **1.08 BPM**

## Automated Tests

`python -m pytest -q`

Result at v2.0 build verification: **7 passed**.

Tests cover:
- adaptive detector behavior across slow, normal, fast, and inverted synthetic ECGs;
- alternate CSV column names;
- millisecond timestamp conversion;
- XLSX ingestion;
- batch failure isolation;
- HRV interval/BPM utilities;
- preprocessing length and sampling-rate-dependent smoothing.

## Ground Truth

The generator's expected beat times are stored in `data/ground_truth.csv`. The normal analyzer does not read this file; it exists only so the detector can be evaluated against known synthetic truth.
