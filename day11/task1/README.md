# Day 11 Task 1: Time Series EDA Pipeline

This task performs an automated exploratory analysis on a time-series dataset stored in `data_set`.

## Expected Input

Place a CSV or Excel file in:

```text
day11/task1/data_set/
```

The script automatically uses the first `.csv`, `.xlsx`, or `.xls` file it finds. The current folder contains a PDF only, so add the actual time-series dataset before running the pipeline.

## Run

From the repository root:

```bash
.venv/bin/python day11/task1/main.py
```

If the script cannot infer the timestamp or target value column, pass them explicitly:

```bash
.venv/bin/python day11/task1/main.py \
  --timestamp-col Date \
  --value-col Sales
```

Optional arguments:

- `--data path/to/file.csv`: use a specific dataset instead of auto-detecting one from `data_set`.
- `--frequency D`: force a pandas time frequency such as `D`, `H`, `W`, or `MS`.
- `--period 12`: force the seasonal period used for decomposition and seasonality checks.

## What The Pipeline Does

1. Checks time continuity and reports missing timestamps.
2. Handles missing target values with time interpolation, forward fill, and backward fill.
3. Generates a time-series plot.
4. Detects trend, seasonality, and outliers.
5. Generates monthly and weekly boxplots.
6. Runs stationarity checks.
7. Generates ACF/PACF plots.
8. Creates feature engineering columns such as month, week, day of week, lags, rolling mean, rolling standard deviation, difference, and percent change.

## Generated Artifacts

All outputs are saved in:

```text
day11/task1/output/
```

Expected files:

- `cleaned_time_series.csv`: original and filled target values on a regular time index.
- `feature_engineered_dataset.csv`: generated time-series features.
- `outliers.csv`: detected outlier timestamps and values.
- `eda_summary.json`: machine-readable EDA summary.
- `eda_report.md`: readable summary report.
- `time_series_plot.png`: target value over time.
- `trend_rolling_plot.png`: rolling mean and rolling standard deviation.
- `monthly_weekly_boxplots.png`: monthly and weekly distribution boxplots.
- `acf_pacf_plot.png`: ACF and PACF view.
- `decomposition_plot.png`: seasonal decomposition plot when `statsmodels` is installed and enough data exists.
