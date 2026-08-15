from pathlib import Path
import pandas as pd
from src.utils.batch import analyze_directory


def test_batch_continues_after_bad_file(tmp_path):
    data_dir = tmp_path / "data"
    out_dir = tmp_path / "out"
    data_dir.mkdir()

    # malformed file: unsupported content/columns
    pd.DataFrame({"x": [1,2,3], "y": [4,5,6]}).to_csv(data_dir / "bad.csv", index=False)

    # Batch should not crash; it should write an error row.
    summary = analyze_directory(data_dir, output_root=out_dir)
    frame = pd.read_csv(summary)
    assert len(frame) == 1
    assert frame.loc[0, "status"].startswith("ERROR:")
