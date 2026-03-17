from __future__ import annotations

import argparse
import logging
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the energy analytics workflow.")
    parser.add_argument(
        "--data-url",
        default=None,
        help="Optional override for the remote UN dataset URL.",
    )
    parser.add_argument(
        "--output",
        default="results",
        help="Directory where generated reports should be written.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        from src.analysis_pipeline import AnalysisPipeline
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("sklearn"):
            raise SystemExit(
                "scikit-learn is required for `run_analysis.py`. Install dependencies with "
                "`python -m pip install -r requirements.txt`."
            ) from exc
        raise

    args = parse_args()
    pipeline = AnalysisPipeline(data_url=args.data_url, output_dir=Path(args.output))
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
