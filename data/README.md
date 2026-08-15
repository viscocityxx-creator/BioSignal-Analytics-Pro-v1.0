# Sample ECG Data

All recordings in `data/ecg/` are **synthetic educational signals**, not human patient data.

The ten files intentionally vary in sampling rate, noise, amplitude, rhythm regularity, orientation, file format, and column naming so v2.0 can exercise adaptive input handling and R-peak detection.

`ground_truth.csv` records the synthetic generator's expected beat times for validation. It is not used by the analyzer during normal processing.
