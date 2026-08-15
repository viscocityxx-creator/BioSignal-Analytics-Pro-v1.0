import pandas as pd
import numpy as np
from src.io.input_loader import load_ecg_file


def test_alternate_csv_columns_and_ms_conversion(tmp_path):
    path = tmp_path / "alternate.csv"
    pd.DataFrame({
        "timestamp_ms": [0, 4, 8, 12],
        "LeadII_mV": [0.1, 0.2, 0.3, 0.2],
    }).to_csv(path, index=False)
    loaded = load_ecg_file(path)
    assert loaded.time_column == "timestamp_ms"
    assert loaded.signal_column == "LeadII_mV"
    assert np.isclose(loaded.frame["Time_s"].iloc[-1], 0.012)


def test_xlsx_input(tmp_path):
    path = tmp_path / "input.xlsx"
    pd.DataFrame({"Time": [0.0, 0.004, 0.008], "Voltage": [0.1, 0.2, 0.1]}).to_excel(path, index=False)
    loaded = load_ecg_file(path)
    assert list(loaded.frame.columns) == ["Time_s", "ECG_mV"]
