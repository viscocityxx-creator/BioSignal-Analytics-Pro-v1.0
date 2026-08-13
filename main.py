
import argparse
from pathlib import Path

from src.analyzers.ecg_analyzer import ECGAnalyzer
from src.utils.batch import analyze_directory

def main():
    parser = argparse.ArgumentParser(
        description="BioSignal Analytics Pro v1.0 - Biomedical ECG analysis platform"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="data/ecg/ecg_patient_001.csv",
        help="Path to an ECG CSV file, or a directory when using --batch"
    )
    parser.add_argument("--batch", action="store_true", help="Analyze every CSV file in a directory")
    parser.add_argument("--output", default="outputs", help="Output directory")
    parser.add_argument("--config", default="config.json", help="Configuration JSON path")
    args = parser.parse_args()

    if args.batch:
        summary = analyze_directory(args.input, output_root=args.output, config_path=args.config)
        print(f"Batch analysis complete: {summary}")
        return

    analyzer = ECGAnalyzer(args.input, config_path=args.config)
    analyzer.analyze(output_root=args.output)
    analyzer.print_summary()

    print("\nGenerated files:")
    for key, value in analyzer.result["output_files"].items():
        print(f"- {key}: {value}")

if __name__ == "__main__":
    main()
