
from pathlib import Path
import json
import numpy as np
import pandas as pd

from src.preprocessing.filters import bandpass_filter, moving_average
from src.signal_processing.peak_detection import detect_r_peaks
from src.signal_processing.hrv import rr_intervals_from_peak_times, bpm_from_rr, hrv_metrics
from src.signal_processing.fft_tools import frequency_spectrum, dominant_frequency
from src.signal_processing.quality import signal_quality_summary
from src.visualization.plots import save_ecg_plot, save_frequency_plot
from src.reports.pdf_report import generate_pdf_report

class ECGAnalyzer:
    REQUIRED_COLUMNS = {"Time_s", "ECG_mV"}

    def __init__(self, filename, config_path="config.json"):
        self.filename = str(filename)
        self.config_path = config_path
        self.df = None
        self.fs = None
        self.peaks = np.array([], dtype=int)
        self.rr = np.array([], dtype=float)
        self.bpm = np.array([], dtype=float)
        self.result = None
        self.config = self._load_config()

    def _load_config(self):
        path = Path(self.config_path)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def load_data(self):
        self.df = pd.read_csv(self.filename)

        missing_cols = self.REQUIRED_COLUMNS - set(self.df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {sorted(missing_cols)}")

        self.df["Time_s"] = pd.to_numeric(self.df["Time_s"], errors="coerce")
        self.df["ECG_mV"] = pd.to_numeric(self.df["ECG_mV"], errors="coerce")

        missing_fraction = float(self.df[["Time_s", "ECG_mV"]].isna().any(axis=1).mean())
        self.df = self.df.dropna(subset=["Time_s", "ECG_mV"]).reset_index(drop=True)
        self.missing_fraction = missing_fraction

        if len(self.df) < 3:
            raise ValueError("ECG file does not contain enough valid samples.")

        dt = np.diff(self.df["Time_s"].to_numpy())
        median_dt = float(np.median(dt))
        if median_dt <= 0:
            raise ValueError("Time column must be strictly increasing.")
        self.fs = 1.0 / median_dt
        return self

    def preprocess(self):
        if self.df is None:
            self.load_data()

        raw = self.df["ECG_mV"].to_numpy(dtype=float)
        lowcut = float(self.config.get("highpass_cutoff_hz", 0.5))
        highcut = float(self.config.get("lowpass_cutoff_hz", 18.0))
        window = int(self.config.get("moving_average_window", 7))

        filtered = bandpass_filter(raw, self.fs, lowcut=lowcut, highcut=highcut, order=4)
        filtered = moving_average(filtered, window=window)
        self.df["Filtered_ECG_mV"] = filtered
        return self

    def detect_peaks(self):
        if "Filtered_ECG_mV" not in self.df.columns:
            self.preprocess()

        self.peaks, self.peak_properties = detect_r_peaks(
            self.df["Filtered_ECG_mV"].to_numpy(),
            fs=self.fs,
            min_distance_seconds=float(self.config.get("peak_min_distance_seconds", 0.45)),
            prominence_factor=float(self.config.get("peak_prominence_factor", 0.55)),
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
            missing_fraction=self.missing_fraction,
        )

        duration = float(self.df["Time_s"].iloc[-1] - self.df["Time_s"].iloc[0])

        self.result = {
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
        for d in [plots_dir, reports_dir, csv_dir]:
            d.mkdir(parents=True, exist_ok=True)

        stem = Path(self.filename).stem
        ecg_plot = plots_dir / f"{stem}_ecg.png"
        spectrum_plot = plots_dir / f"{stem}_spectrum.png"
        pdf_report = reports_dir / f"{stem}_report.pdf"
        metrics_csv = csv_dir / f"{stem}_metrics.csv"
        annotated_csv = csv_dir / f"{stem}_annotated.csv"

        save_ecg_plot(
            self.df["Time_s"],
            self.df["ECG_mV"],
            self.df["Filtered_ECG_mV"].to_numpy(),
            self.peaks,
            ecg_plot,
            title=f"ECG Analysis - {stem}"
        )

        freq, mag = frequency_spectrum(self.df["Filtered_ECG_mV"].to_numpy(), self.fs)
        save_frequency_plot(freq, mag, spectrum_plot, title=f"Frequency Spectrum - {stem}")

        export_df = self.df.copy()
        export_df["R_Peak"] = False
        if len(self.peaks):
            export_df.loc[self.peaks, "R_Peak"] = True
        export_df.to_csv(annotated_csv, index=False)

        flat_result = {
            key: value
            for key, value in self.result.items()
            if key != "signal_quality"
        }
        flat_result["signal_quality_rating"] = self.result["signal_quality"]["rating"]
        flat_result["quality_issues"] = "; ".join(self.result["signal_quality"].get("issues", []))
        pd.DataFrame([flat_result]).to_csv(metrics_csv, index=False)

        generate_pdf_report(
            self.result,
            str(ecg_plot),
            str(spectrum_plot),
            str(pdf_report),
        )

        self.result["output_files"] = {
            "ecg_plot": str(ecg_plot),
            "spectrum_plot": str(spectrum_plot),
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
        print("=" * 68)
        print("BIOSIGNAL ANALYTICS PRO v1.0 - ECG REPORT")
        print("=" * 68)
        print(f"File                 : {r['filename']}")
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
        print(f"Dominant frequency   : {_fmt(r['dominant_frequency_hz'])} Hz")
        print(f"Signal quality       : {r['signal_quality']['rating']}")
        print("=" * 68)

def _fmt(value):
    return "N/A" if value is None else f"{float(value):.2f}"
