# Energy Outlook Navigator

Energy Outlook Navigator is a business-oriented Streamlit application that helps teams quickly understand the present state and likely near-term direction of country energy systems using official United Nations energy data.

It is designed for strategy, market scanning, policy review, investment research, and executive reporting. Users can open the dashboard, choose a country, review the latest energy position, inspect historical performance, and view simple forward-looking projections. They can also get a fast global snapshot to see how world energy trends are shifting.

## Business Purpose

This project helps decision-makers answer questions such as:

- How much energy supply does a country currently have?
- Is the country behaving more like a net importer or exporter?
- How are production, imports, and per-capita supply changing over time?
- What does a simple directional forecast suggest for the next few years?
- Which countries currently lead world energy supply?
- What broad world trend should an executive notice immediately?

## What Users Can Do

- View a global executive dashboard with world supply, average per-capita supply, importer share, and country coverage.
- Explore any country in the dataset and see its latest energy indicators.
- Review country history through trend charts.
- Generate quick directional forecasts for core metrics.
- Compare countries through a latest-year global ranking table.
- Pull fresh data from the official UN source at runtime.

## Main Experience

The Streamlit app includes three business views:

1. Executive Overview
   World headline metrics and a quick global trend snapshot.
2. Country Explorer
   Current-country snapshot, historical trends, and simple forecast outlooks.
3. World Trends
   Global time series and latest rankings for a fast market scan.

## Run The Dashboard

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Command-Line Analysis

If you still want the original model-comparison workflow, you can run:

```bash
python run_analysis.py
```

## Data Source

The application downloads the latest compatible UN energy dataset at runtime. You can override the remote source with `--data-url` in the CLI flow or by editing the sidebar input in the Streamlit app.

## Important Forecast Note

The forecasts in the dashboard are simple linear trend projections built for fast business scanning. They are useful for directional planning, but they are not a substitute for a full econometric or scenario-based forecasting model.

## Testing

```bash
python -m unittest discover -s tests
```
