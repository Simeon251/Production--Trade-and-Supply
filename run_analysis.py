from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.analysis_pipeline import AnalysisPipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the energy analytics workflow.")
    parser.add_argument(
        "--data",
        default="dataset/Production,Trade and Supply of Energy.csv",
        help="Path to the raw CSV dataset.",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Directory where generated reports should be written.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args()
    pipeline = AnalysisPipeline(data_path=Path(args.data), output_dir=Path(args.output))
    results = pipeline.run()

    for hypothesis_key in ["hypothesis_1", "hypothesis_2", "hypothesis_3"]:
        section = results[hypothesis_key]
        best = section["comparison"][0]
        primary_metric = "Accuracy" if "Accuracy" in best else "R2 Score"
        print(
            f"{hypothesis_key}: {section['best_model']} | "
            f"{primary_metric}={best[primary_metric]:.4f} | decision={section['decision']}"
        )


if __name__ == "__main__":
    main()
