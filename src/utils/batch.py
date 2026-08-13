
from pathlib import Path
import pandas as pd
from src.analyzers.ecg_analyzer import ECGAnalyzer

def analyze_directory(input_dir, output_root="outputs", config_path="config.json"):
    input_dir = Path(input_dir)
    files = sorted(input_dir.glob("*.csv"))
    rows = []

    for file in files:
        try:
            analyzer = ECGAnalyzer(file, config_path=config_path)
            analyzer.analyze(output_root=output_root)
            analyzer.print_summary()
            result = analyzer.result.copy()
            quality = result.pop("signal_quality")
            result.pop("output_files", None)
            result["signal_quality_rating"] = quality["rating"]
            result["status"] = "OK"
            rows.append(result)
        except Exception as exc:
            rows.append({
                "filename": file.name,
                "status": f"ERROR: {exc}"
            })

    summary_path = Path(output_root) / "csv" / "batch_summary.csv"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(summary_path, index=False)
    return summary_path
