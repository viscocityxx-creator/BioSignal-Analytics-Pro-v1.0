from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import numpy as np
import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@dataclass
class LoadedSignal:
    frame: pd.DataFrame
    time_column: str
    signal_column: str
    time_unit: str
    signal_unit: str
    source_format: str


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(name).strip().lower()).strip("_")


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix == ".xlsx":
        return pd.read_excel(path, engine="openpyxl")
    if suffix == ".xls":
        return pd.read_excel(path, engine="xlrd")
    raise ValueError(
        f"Unsupported file type '{suffix}'. Supported formats: CSV, XLSX, XLS."
    )


def _pick_column(columns, role: str) -> str:
    normalized = {col: _normalize(col) for col in columns}

    if role == "time":
        exact = {
            "time_s", "time_sec", "time_seconds", "seconds", "second",
            "time_ms", "timestamp_ms", "elapsed_time_s", "elapsed_seconds",
            "timestamp", "time"
        }
        keywords = ("time", "timestamp", "second", "elapsed")
    else:
        exact = {
            "ecg_mv", "ecg", "voltage", "voltage_mv", "lead_ii", "leadii",
            "lead_ii_mv", "signal", "signal_mv", "ecg_voltage"
        }
        keywords = ("ecg", "lead", "voltage", "signal")

    exact_matches = [col for col, norm in normalized.items() if norm in exact]
    if len(exact_matches) == 1:
        return exact_matches[0]

    scored = []
    for col, norm in normalized.items():
        score = sum(1 for kw in keywords if kw in norm)
        if role == "signal" and ("time" in norm or "timestamp" in norm):
            score = 0
        if score:
            scored.append((score, col))

    scored.sort(reverse=True)
    if scored and (len(scored) == 1 or scored[0][0] > scored[1][0]):
        return scored[0][1]

    raise ValueError(
        f"Could not uniquely identify the {role} column. Columns found: {list(columns)}"
    )


def _time_scale_from_name(column: str) -> tuple[float, str]:
    norm = _normalize(column)
    if "ms" in norm or "millisecond" in norm:
        return 0.001, "ms"
    if "us" in norm or "microsecond" in norm:
        return 1e-6, "us"
    return 1.0, "s"


def _signal_scale_from_name(column: str) -> tuple[float, str]:
    norm = _normalize(column)
    if "uv" in norm or "microvolt" in norm:
        return 0.001, "uV"
    # Only interpret explicit *_v names as volts; generic "voltage" is left unchanged.
    if norm.endswith("_v") and not norm.endswith("_mv"):
        return 1000.0, "V"
    return 1.0, "mV"


def load_ecg_file(filename: str | Path) -> LoadedSignal:
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{path.suffix}'. Supported formats: CSV, XLSX, XLS."
        )

    raw = _read_table(path)
    if raw.empty:
        raise ValueError("Input file is empty.")

    time_col = _pick_column(raw.columns, "time")
    signal_col = _pick_column(raw.columns, "signal")

    time_scale, time_unit = _time_scale_from_name(time_col)
    signal_scale, signal_unit = _signal_scale_from_name(signal_col)

    frame = pd.DataFrame({
        "Time_s": pd.to_numeric(raw[time_col], errors="coerce") * time_scale,
        "ECG_mV": pd.to_numeric(raw[signal_col], errors="coerce") * signal_scale,
    })

    return LoadedSignal(
        frame=frame,
        time_column=str(time_col),
        signal_column=str(signal_col),
        time_unit=time_unit,
        signal_unit=signal_unit,
        source_format=path.suffix.lower().lstrip("."),
    )
