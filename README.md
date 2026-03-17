# Energy Production, Trade, and Supply Analysis

Production-grade predictive analytics workflow built on the United Nations energy production, trade, and supply dataset. The project packages the original coursework into a cleaner, reproducible repository with a proper command-line entrypoint, safer model evaluation, and lightweight automated tests.

## What Changed

- Replaced notebook-only execution with a reusable Python pipeline in `src/analysis_pipeline.py`.
- Fixed train/test leakage by fitting models on training folds instead of the full dataset.
- Added packaging metadata in `pyproject.toml`.
- Added automated regression checks in `tests/test_project.py`.
- Added repo hygiene with `.gitignore`.

## Project Structure

```text
.
|-- dataset/
|-- notebooks/
|-- results/
|-- src/
|   |-- analysis_pipeline.py
|   |-- data_processor.py
|   |-- feature_engineer.py
|   |-- model_evaluator.py
|   `-- model_trainer.py
|-- tests/
|-- pyproject.toml
`-- run_analysis.py
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python run_analysis.py
```

The pipeline writes a machine-readable summary to `results/analysis_summary.json` and prints the best model for each hypothesis.

## Hypotheses Covered

1. Total energy supply can be predicted from production, imports, and stock changes.
2. Importer versus exporter status can be classified from energy balance indicators.
3. Per-capita energy supply can be predicted from supply and production patterns.

## Development

Run the local regression checks with:

```bash
python -m unittest discover -s tests
```

## Notes

- The notebook is retained for exploration, but the CLI pipeline is now the supported execution path.
- Generated outputs under `results/` are intentionally ignored so the repository stays clean.
