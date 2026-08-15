from pathlib import Path
import numpy as np
import pandas as pd

from src.io.input_loader import load_ecg_file
from src.preprocessing.filters import adaptive_bandpass_filter, adaptive_smoothing_window, moving_average
from src.signal_processing.peak_detection import detect_r_peaks
from src.signal_processing.hrv import rr_intervals_from_peak_times, bpm_from_rr, hrv_metrics
from src.signal_processing.fft_tools import frequency_spectrum, dominant_frequency
from src.signal_processing.quality import signal_quality_summary
from src.visualization.plots import save_ecg_plot, save_frequency_plot, save_rr_bpm_plot
from src.reports.pdf_report import generate_pdf_report
from src.utils.logging_config import configure_logging
from src.version import __version__


class ECGAnalyzer:
    def __init__(self, filename, config_path=None):
        self.filename = str(filename)
        self.config_path = config_path  # retained for backward compatibility; peak detection is adaptive in v2
        self.df = None
        self.fs = None
        self.peaks = np.array([], dtype=int)
        self.rr = np.array([], dtype=float)
        self.bpm = np.array([], dtype=float)
        self.result = None
        self.input_metadata = {}
        self.filter_metadata = {}
        self.logger = configure_logging()

    def load_data(self):
        loaded = load_ecg_file(self.filename)
        self.df = loaded.frame.copy()
        self.input_metadata = {
            "time_column": loaded.time_column,
            "signal_column": loaded.signal_column,
            "time_unit_detected": loaded.time_unit,
            "signal_unit_detected": loaded.signal_unit,
            "source_format": loaded.source_format,
        }

        missing_fraction = float(self.df[["Time_s", "ECG_mV"]].isna().any(axis=1).mean())
        self.df = self.df.dropna(subset=["Time_s", "ECG_mV"]).reset_index(drop=True)
        self.missing_fraction = missing_fraction

        if len(self.df) < 10:
            raise ValueError("ECG file does not contain enough valid samples.")

        time_values = self.df["Time_s"].to_numpy(dtype=float)
        dt = np.diff(time_values)
        if np.any(~np.isfinite(dt)) or np.any(dt <= 0):
            raise ValueError("Time values must be finite and strictly increasing.")

        median_dt = float(np.median(dt))
        self.fs = 1.0 / median_dt
        if not np.isfinite(self.fs) or self.fs <= 0:
            raise ValueError("Unable to estimate a valid sampling frequency.")

        self.logger.info("Loaded %s | format=%s | fs=%.3f Hz", self.filename, loaded.source_format, self.fs)
        return self

    def preprocess(self):
        if self.df is None:
            self.load_data()

        raw = self.df["ECG_mV"].to_numpy(dtype=float)
        filtered, filter_meta = adaptive_bandpass_filter(raw, self.fs, order=4)
        window = adaptive_smoothing_window(self.fs)
        filtered = moving_average(filtered, window=window)

        self.df["Filtered_ECG_mV"] = filtered
        self.filter_metadata = {**filter_meta, "smoothing_window_samples": int(window)}
        return self

    def detect_peaks(self):
        if self.df is None or "Filtered_ECG_mV" not in self.df.columns:
            self.preprocess()

        self.peaks, self.peak_properties = detect_r_peaks(
            self.df["Filtered_ECG_mV"].to_numpy(dtype=float),
            fs=self.fs,
        )
        self.logger.info(
            "Adaptive peak detection | file=%s | beats=%d | estimated_rr=%.4f",
            Path(self.filename).name,
            len(self.peaks),
            float(self.peak_properties.get("estimated_rr_s", 0.0)),
        )
        return self

    def calculate_metrics(self):
        if len(self.peaks) == 0:
            self.detect_peaks()

        peak_times = self.df["Time_s"].iloc[self.peaks].to_numpy(dtype=float)
        self.rr = rr_intervals_from_peak_times(peak_times)
        self.bpm = bpm_from_rr(self.rr)
        hrv = hrv_metrics(self.rr)

        filtered = self.df["Filtered_ECG_mV"].to_numpy(dtype=float)
        dominant = dominant_frequency(filtered, self.fs)
        quality = signal_quality_summary(
            self.df["ECG_mV"].to_numpy(dtype=float),
            filtered,
            self.bpm,
            self.rr,
            missing_fraction=self.missing_fraction,
        )

        duration = float(self.df["Time_s"].iloc[-1] - self.df["Time_s"].iloc[0])
        adaptive_meta = {
            key: value for key, value in self.peak_properties.items()
            if key in {
                "method", "estimated_rr_s", "derived_min_distance_samples",
                "derived_min_distance_s", "derived_prominence", "robust_signal_sigma",
                "integration_window_samples", "candidate_count"
            }
        }

        self.result = {
            "software_version": __version__,
            "filename": Path(self.filename).name,
            "samples": int(len(self.df)),
            "sampling_frequency_hz": float(self.fs),
            "duration_s": duration,
            "detected_beats": int(len(self.peaks)),
            "average_bpm": float(np.mean(self.bpm)) if len(self.bpm) else None,
            "minimum_bpm": float(np.min(self.bpm)) if len(self.bpm) else None,
            "maximum_bpm": float(np.max(self.bpm)) if len(self.bpm) else None,
            "mean_rr_s": hrv["mean_rr_s"],
            "sdnn_ms": hrv["sdnn_ms"],
            "rmssd_ms": hrv["rmssd_ms"],
            "dominant_frequency_hz": dominant,
            "input_metadata": self.input_metadata,
            "filter_metadata": self.filter_metadata,
            "adaptive_detection": adaptive_meta,
            "signal_quality": quality,
        }
        return self

    def export(self, output_root="outputs"):
        if self.result is None:
            self.calculate_metrics()

        output_root = Path(output_root)
        plots_dir = output_root / "plots"
        reports_dir = output_root / "reports"
        csv_dir = output_root / "csv"
        for directory in [plots_dir, reports_dir, csv_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        stem = Path(self.filename).stem
        ecg_plot = plots_dir / f"{stem}_ecg.png"
        spectrum_plot = plots_dir / f"{stem}_spectrum.png"
        rr_plot = plots_dir / f"{stem}_rr_bpm.png"
        pdf_report = reports_dir / f"{stem}_report.pdf"
        metrics_csv = csv_dir / f"{stem}_metrics.csv"
        annotated_csv = csv_dir / f"{stem}_annotated.csv"

        filtered = self.df["Filtered_ECG_mV"].to_numpy(dtype=float)
        peak_times = self.df["Time_s"].iloc[self.peaks].to_numpy(dtype=float)

        save_ecg_plot(self.df["Time_s"], self.df["ECG_mV"], filtered, self.peaks, ecg_plot, title=f"ECG Analysis - {stem}")
        freq, mag = frequency_spectrum(filtered, self.fs)
        save_frequency_plot(freq, mag, spectrum_plot, title=f"Frequency Spectrum - {stem}")
        save_rr_bpm_plot(peak_times, self.rr, self.bpm, rr_plot, title=f"Beat-to-Beat Trend - {stem}")

        export_df = self.df.copy()
        export_df["R_Peak"] = False
        if len(self.peaks):
            export_df.loc[self.peaks, "R_Peak"] = True
        export_df.to_csv(annotated_csv, index=False)

        flat_result = {
            "software_version": self.result["software_version"],
            "filename": self.result["filename"],
            "samples": self.result["samples"],
            "sampling_frequency_hz": self.result["sampling_frequency_hz"],
            "duration_s": self.result["duration_s"],
            "detected_beats": self.result["detected_beats"],
            "average_bpm": self.result["average_bpm"],
            "minimum_bpm": self.result["minimum_bpm"],
            "maximum_bpm": self.result["maximum_bpm"],
            "mean_rr_s": self.result["mean_rr_s"],
            "sdnn_ms": self.result["sdnn_ms"],
            "rmssd_ms": self.result["rmssd_ms"],
            "dominant_frequency_hz": self.result["dominant_frequency_hz"],
            "signal_quality_score": self.result["signal_quality"]["score"],
            "signal_quality_rating": self.result["signal_quality"]["rating"],
            "source_format": self.input_metadata.get("source_format"),
            "mapped_time_column": self.input_metadata.get("time_column"),
            "mapped_signal_column": self.input_metadata.get("signal_column"),
            "adaptive_estimated_rr_s": self.result["adaptive_detection"].get("estimated_rr_s"),
            "adaptive_min_distance_s": self.result["adaptive_detection"].get("derived_min_distance_s"),
            "adaptive_prominence": self.result["adaptive_detection"].get("derived_prominence"),
            "quality_issues": "; ".join(self.result["signal_quality"].get("issues", [])),
        }
        pd.DataFrame([flat_result]).to_csv(metrics_csv, index=False)

        generate_pdf_report(self.result, str(ecg_plot), str(spectrum_plot), str(rr_plot), str(pdf_report))

        self.result["output_files"] = {
            "ecg_plot": str(ecg_plot),
            "spectrum_plot": str(spectrum_plot),
            "rr_bpm_plot": str(rr_plot),
            "pdf_report": str(pdf_report),
            "metrics_csv": str(metrics_csv),
            "annotated_csv": str(annotated_csv),
        }
        return self

    def analyze(self, output_root="outputs"):
        return self.load_data().preprocess().detect_peaks().calculate_metrics().export(output_root)

    def print_summary(self):
        if self.result is None:
            self.calculate_metrics()
        r = self.result
        print("=" * 72)
        print(f"BIOSIGNAL ANALYTICS PRO v{__version__} - ADAPTIVE ECG REPORT")
        print("=" * 72)
        print(f"File                 : {r['filename']}")
        print(f"Input format         : {r['input_metadata']['source_format'].upper()}")
        print(f"Mapped columns       : {r['input_metadata']['time_column']} / {r['input_metadata']['signal_column']}")
        print(f"Samples              : {r['samples']}")
        print(f"Sampling frequency   : {r['sampling_frequency_hz']:.2f} Hz")
        print(f"Recording duration   : {r['duration_s']:.2f} s")
        print(f"Detected beats       : {r['detected_beats']}")
        print(f"Average BPM          : {_fmt(r['average_bpm'])}")
        print(f"Minimum BPM          : {_fmt(r['minimum_bpm'])}")
        print(f"Maximum BPM          : {_fmt(r['maximum_bpm'])}")
        print(f"Mean RR interval     : {_fmt(r['mean_rr_s'])} s")
        print(f"SDNN                 : {_fmt(r['sdnn_ms'])} ms")
        print(f"RMSSD                : {_fmt(r['rmssd_ms'])} ms")
        print(f"Adaptive RR estimate : {_fmt(r['adaptive_detection'].get('estimated_rr_s'))} s")
        print(f"Quality              : {r['signal_quality']['rating']} ({r['signal_quality']['score']:.0f}/100)")
        print("=" * 72)


def _fmt(value):
    return "N/A" if value is None else f"{float(value):.2f}"
