import argparse
from pathlib import Path

from src.analyzers.ecg_analyzer import ECGAnalyzer
from src.utils.batch import analyze_directory
from src.version import __version__


def main():
    parser = argparse.ArgumentParser(
        description=f"BioSignal Analytics Pro v{__version__} - Adaptive ECG analysis platform"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=None,
        help="ECG file path. If omitted, the sample data folder is analyzed in batch mode."
    )
    parser.add_argument("--batch", action="store_true", help="Analyze every supported file in a directory")
    parser.add_argument("--output", default="outputs", help="Output directory")
    args = parser.parse_args()

    # v2 removes the v1 hard-coded patient_001 default.
    if args.input is None:
        analyze_directory("data/ecg", output_root=args.output)
        return

    input_path = Path(args.input)
    if args.batch or input_path.is_dir():
        analyze_directory(input_path, output_root=args.output)
        return

    analyzer = ECGAnalyzer(input_path)
    analyzer.analyze(output_root=args.output)
    analyzer.print_summary()

    print("\nGenerated files:")
    for key, value in analyzer.result["output_files"].items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
