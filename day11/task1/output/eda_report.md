# Time Series EDA Report

- Dataset: `/Users/jagat/Documents/python_training/day11/task1/data_set/sakshi_rr_intervals_20260611T074737_len128s.csv`
- Rows loaded: 88
- Timestamp column: `mid_timestamp_ms`
- Target column: `rr_ms`

## Feature Engineering Columns

`value`, `year`, `quarter`, `month`, `week_of_year`, `day_of_month`, `day_of_week`, `is_weekend`, `lag_1`, `lag_7`, `rolling_mean_7`, `rolling_std_7`, `diff_1`, `pct_change_1`

## Continuity and Missing Values

{
  "expected_timestamps": null,
  "actual_timestamps": 88,
  "missing_timestamps": null,
  "missing_timestamp_examples": [],
  "regular_frequency_detected": false,
  "median_gap": "0 days 00:00:00.746000",
  "max_gap": "0 days 00:00:11.562000",
  "original_missing_target_values": 0,
  "missing_after_fill": 0,
  "fill_strategy": "time interpolation, then forward fill, then backward fill",
  "frequency": null
}

## Trend

{
  "trend_direction": "downward",
  "linear_slope_per_step": -2.4820277552745558,
  "start_value": 681.0,
  "end_value": 719.0
}

## Seasonality

{
  "period": 12,
  "seasonality_detected": false,
  "autocorrelation_at_period": -0.08392360005753997
}

## Stationarity

{
  "method": "rolling statistics",
  "adf_available": false,
  "rolling_mean_start": 685.1666666666666,
  "rolling_mean_end": 504.3333333333333,
  "variance_ratio_second_half_to_first_half": 0.916596597386185
}

## Outliers

Detected outliers: 0

## Generated Plots

- `time_series_plot.png`
- `trend_rolling_plot.png`
- `monthly_weekly_boxplots.png`
- `acf_pacf_plot.png`
