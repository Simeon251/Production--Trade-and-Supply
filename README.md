# Energy Production, Trade, and Supply Analysis

Predictive analytics workflow for the United Nations energy production, trade, and supply dataset. The project now pulls fresh data from the official UN remote endpoint at runtime instead of relying on a committed local CSV snapshot.

## What Changed

- Fetches the source dataset over HTTP from the official UN data endpoint.
- Keeps the cleaned modeling pipeline and holdout-based evaluation flow.
- Writes a machine-readable summary to `results/analysis_summary.json`.
- Uses mocked network responses in tests so the test suite stays fast and deterministic.

## Quick Start

```bash
python -m pip install -r requirements.txt
python run_analysis.py
```

Optionally override the source URL:

```bash
python run_analysis.py --data-url "https://data.un.org/_Docs/SYB/CSV/SYB68_263_202511_Production%2C%20Trade%20and%20Supply%20of%20Energy.csv"
```

## Development

```bash
python -m unittest discover -s tests
```

## Notes

- The pipeline tries the current official UN CSV URL first and falls back to the previous official release if needed.
- You can also set `UN_ENERGY_DATA_URL` to point at a different compatible remote source.
