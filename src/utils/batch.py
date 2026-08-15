from pathlib import Path
import pandas as pd
from src.analyzers.ecg_analyzer import ECGAnalyzer
from src.io.input_loader import SUPPORTED_EXTENSIONS
from src.utils.logging_config import configure_logging


def analyze_directory(input_dir, output_root="outputs", config_path=None):
    input_dir = Path(input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        raise ValueError(f"Batch input directory does not exist: {input_dir}")

    files = sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS)
    if not files:
        raise ValueError(f"No supported ECG files found in {input_dir}")

    logger = configure_logging()
    rows = []
    print(f"Batch analysis: {len(files)} supported files found in {input_dir}")

    for number, file in enumerate(files, start=1):
        print(f"[{number}/{len(files)}] {file.name}")
        try:
            analyzer = ECGAnalyzer(file, config_path=config_path)
            analyzer.analyze(output_root=output_root)
            result = analyzer.result
            rows.append({
                "filename": result["filename"],
                "status": "OK",
                "detected_beats": result["detected_beats"],
                "average_bpm": result["average_bpm"],
                "signal_quality_score": result["signal_quality"]["score"],
                "signal_quality_rating": result["signal_quality"]["rating"],
                "source_format": result["input_metadata"]["source_format"],
                "sampling_frequency_hz": result["sampling_frequency_hz"],
            })
        except Exception as exc:
            logger.exception("Batch failure | file=%s", file)
            rows.append({"filename": file.name, "status": f"ERROR: {exc}"})
            print(f"    ERROR: {exc}")

    summary_path = Path(output_root) / "csv" / "batch_summary.csv"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(summary_path, index=False)

    ok = sum(row["status"] == "OK" for row in rows)
    failed = len(rows) - ok
    print(f"Batch complete: {ok} succeeded, {failed} failed")
    print(f"Summary: {summary_path}")
    return summary_path
