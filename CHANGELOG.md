# Changelog

## v2.0.0 — Adaptive Signal Processing Engine

### Added
- Adaptive R-peak detector using QRS energy, robust signal statistics, and autocorrelation-derived R-R periodicity.
- CSV, XLSX, and XLS input support.
- Automatic time-column and ECG-signal column mapping.
- Automatic millisecond-to-second conversion when indicated by column naming.
- Structured analysis logging.
- Batch processing that continues after individual file failures.
- R-R/BPM trend plots.
- Adaptive processing metadata in CSV and PDF reports.
- Signal-quality score and engineering review notes.
- Expanded automated tests.

### Changed
- Removed the v1 hard-coded default input file (`ecg_patient_001.csv`).
- Running `python main.py` now analyzes every supported file in `data/ecg/`.
- Peak spacing and prominence are no longer read from fixed configuration values.
- Input loading is separated from ECG analysis logic.

### Important
The adaptive detector and quality score are engineering heuristics for a portfolio project. They are not clinically validated.
