from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".cache"
CACHE_DIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(CACHE_DIR / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller

    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False


DATA_DIR = BASE_DIR / "data_set"
OUTPUT_DIR = BASE_DIR / "output"


@dataclass
class TimeSeriesConfig:
    data_path: Path
    timestamp_col: str | None
    value_col: str | None
    frequency: str | None
    period: int | None


def parse_args() -> TimeSeriesConfig:
    parser = argparse.ArgumentParser(
        description="Run time-series EDA for the dataset inside day11/task1/data_set."
    )
    parser.add_argument("--data", type=Path, default=None, help="Optional CSV/XLSX file path.")
    parser.add_argument("--timestamp-col", default=None, help="Timestamp/date column name.")
    parser.add_argument("--value-col", default=None, help="Numeric target column name.")
    parser.add_argument("--frequency", default=None, help="Optional pandas frequency, e.g. D, H, MS.")
    parser.add_argument("--period", type=int, default=None, help="Seasonal period for decomposition.")
    args = parser.parse_args()

    data_path = args.data or find_dataset(DATA_DIR)
    return TimeSeriesConfig(
        data_path=data_path,
        timestamp_col=args.timestamp_col,
        value_col=args.value_col,
        frequency=args.frequency,
        period=args.period,
    )


def find_dataset(data_dir: Path) -> Path:
    allowed = ("*.csv", "*.xlsx", "*.xls")
    candidates: list[Path] = []
    for pattern in allowed:
        candidates.extend(sorted(data_dir.glob(pattern)))

    if not candidates:
        found = ", ".join(path.name for path in sorted(data_dir.glob("*"))) or "no files"
        raise FileNotFoundError(
            f"No CSV/XLSX dataset found in {data_dir}. Found: {found}. "
            "Place the time-series dataset there or pass --data path/to/file.csv."
        )
    return candidates[0]


def load_data(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported dataset format: {path.suffix}")


def infer_timestamp_column(df: pd.DataFrame, requested: str | None) -> str:
    if requested:
        ensure_column(df, requested)
        return requested

    preferred_names = (
        "mid_timestamp_ms",
        "mid_elapsed_ms",
        "timestamp",
        "datetime",
        "date",
        "time",
        "elapsed",
        "ds",
    )
    exact_matches = [col for col in df.columns if col.lower() in preferred_names]
    if exact_matches:
        return exact_matches[0]

    likely_names = ("date", "time", "timestamp", "datetime", "elapsed", "ds")
    named_candidates = [
        col for col in df.columns if any(token in col.lower() for token in likely_names)
    ]
    for col in named_candidates + list(df.columns):
        converted = convert_to_datetime(df[col], col)
        if converted.notna().mean() >= 0.8:
            return col

    raise ValueError("Could not infer timestamp column. Re-run with --timestamp-col COLUMN.")


def infer_value_column(df: pd.DataFrame, timestamp_col: str, requested: str | None) -> str:
    if requested:
        ensure_column(df, requested)
        return requested

    preferred_value_names = (
        "rr_ms",
        "value",
        "target",
        "y",
        "sales",
        "price",
        "count",
        "temperature",
        "demand",
    )
    for name in preferred_value_names:
        for col in df.columns:
            if col != timestamp_col and col.lower() == name:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if df[col].notna().mean() >= 0.8:
                    return col

    numeric_cols = [
        col for col in df.select_dtypes(include=np.number).columns if col != timestamp_col
    ]
    numeric_cols = [
        col
        for col in numeric_cols
        if not col.lower().endswith("_id")
        and col.lower() != "id"
        and "timestamp" not in col.lower()
        and "elapsed" not in col.lower()
    ]
    if not numeric_cols:
        for col in df.columns:
            if col == timestamp_col:
                continue
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().mean() >= 0.8:
                df[col] = converted
                numeric_cols.append(col)

    if not numeric_cols:
        raise ValueError("Could not infer numeric target column. Re-run with --value-col COLUMN.")

    return max(numeric_cols, key=lambda col: df[col].notna().sum())


def convert_to_datetime(values: pd.Series, column_name: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    name = column_name.lower()
    if numeric.notna().mean() >= 0.8 and name.endswith("_ms"):
        return pd.to_datetime(numeric, unit="ms", errors="coerce")
    if numeric.notna().mean() >= 0.8 and "elapsed" in name:
        return pd.to_datetime(numeric, unit="ms", errors="coerce")
    return pd.to_datetime(values, errors="coerce")


def ensure_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        raise ValueError(f"Column '{column}' was not found. Available columns: {list(df.columns)}")


def prepare_series(
    df: pd.DataFrame,
    timestamp_col: str,
    value_col: str,
    frequency: str | None,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    working = df.copy()
    working[timestamp_col] = convert_to_datetime(working[timestamp_col], timestamp_col)
    working[value_col] = pd.to_numeric(working[value_col], errors="coerce")
    working = working.dropna(subset=[timestamp_col]).sort_values(timestamp_col)
    working = working.drop_duplicates(subset=[timestamp_col], keep="last")
    working = working.set_index(timestamp_col)

    inferred_frequency = frequency or pd.infer_freq(working.index)
    if inferred_frequency is None:
        inferred_frequency = infer_regular_frequency(working.index)

    continuity = check_time_continuity(working.index, inferred_frequency)
    if inferred_frequency:
        working = working.asfreq(inferred_frequency)

    raw_missing = int(working[value_col].isna().sum())
    filled = fill_missing_values(working[value_col])
    working[f"{value_col}_filled"] = filled

    missing_summary = {
        "original_missing_target_values": raw_missing,
        "missing_after_fill": int(filled.isna().sum()),
        "fill_strategy": "time interpolation, then forward fill, then backward fill",
    }
    return working, filled, {**continuity, **missing_summary, "frequency": inferred_frequency}


def infer_regular_frequency(index: pd.DatetimeIndex) -> str | None:
    if len(index) < 3:
        return None
    deltas = index.to_series().diff().dropna()
    if deltas.empty:
        return None
    mode_delta = deltas.mode().iloc[0]
    regularity_ratio = float((deltas == mode_delta).mean())
    if regularity_ratio < 0.8:
        return None
    return pd.tseries.frequencies.to_offset(mode_delta).freqstr


def check_time_continuity(index: pd.DatetimeIndex, frequency: str | None) -> dict:
    if not frequency or index.empty:
        gaps = index.to_series().diff().dropna()
        return {
            "expected_timestamps": None,
            "actual_timestamps": int(len(index)),
            "missing_timestamps": None,
            "missing_timestamp_examples": [],
            "regular_frequency_detected": False,
            "median_gap": str(gaps.median()) if not gaps.empty else None,
            "max_gap": str(gaps.max()) if not gaps.empty else None,
        }

    full_index = pd.date_range(index.min(), index.max(), freq=frequency)
    missing = full_index.difference(index)
    return {
        "expected_timestamps": int(len(full_index)),
        "actual_timestamps": int(len(index)),
        "missing_timestamps": int(len(missing)),
        "missing_timestamp_examples": [str(item) for item in missing[:10]],
    }


def fill_missing_values(series: pd.Series) -> pd.Series:
    return series.interpolate(method="time", limit_direction="both").ffill().bfill()


def create_feature_engineering_columns(series: pd.Series) -> pd.DataFrame:
    features = pd.DataFrame({"value": series})
    features["year"] = features.index.year
    features["quarter"] = features.index.quarter
    features["month"] = features.index.month
    features["week_of_year"] = features.index.isocalendar().week.astype(int)
    features["day_of_month"] = features.index.day
    features["day_of_week"] = features.index.dayofweek
    features["is_weekend"] = features["day_of_week"].isin([5, 6]).astype(int)
    features["lag_1"] = series.shift(1)
    features["lag_7"] = series.shift(7)
    features["rolling_mean_7"] = series.rolling(7, min_periods=2).mean()
    features["rolling_std_7"] = series.rolling(7, min_periods=2).std()
    features["diff_1"] = series.diff()
    features["pct_change_1"] = series.pct_change(fill_method=None)
    return features


def estimate_period(series: pd.Series, frequency: str | None, requested_period: int | None) -> int:
    if requested_period:
        return requested_period
    if not frequency:
        return min(12, max(2, len(series) // 4))

    freq_upper = frequency.upper()
    if "H" in freq_upper:
        return 24
    if freq_upper.startswith("D"):
        return 7
    if freq_upper.startswith("W"):
        return 52 if len(series) >= 104 else 4
    if freq_upper.startswith("M"):
        return 12
    if freq_upper.startswith("Q"):
        return 4
    return min(12, max(2, len(series) // 4))


def detect_outliers(series: pd.Series) -> pd.DataFrame:
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    z_score = (series - series.mean()) / series.std(ddof=0)
    outlier_mask = (series < lower) | (series > upper) | (z_score.abs() > 3)
    return pd.DataFrame(
        {
            "timestamp": series.index[outlier_mask].astype(str),
            "value": series[outlier_mask].values,
            "z_score": z_score[outlier_mask].values,
            "iqr_lower": lower,
            "iqr_upper": upper,
        }
    )


def trend_summary(series: pd.Series) -> dict:
    clean = series.dropna()
    x = np.arange(len(clean))
    slope = float(np.polyfit(x, clean.values, 1)[0]) if len(clean) > 1 else 0.0
    direction = "upward" if slope > 0 else "downward" if slope < 0 else "flat"
    return {
        "trend_direction": direction,
        "linear_slope_per_step": slope,
        "start_value": float(clean.iloc[0]) if len(clean) else None,
        "end_value": float(clean.iloc[-1]) if len(clean) else None,
    }


def seasonality_summary(series: pd.Series, period: int) -> dict:
    if period < 2 or len(series.dropna()) < period * 2:
        return {
            "period": period,
            "seasonality_detected": False,
            "reason": "Not enough observations for two full seasonal cycles.",
        }
    autocorrelation = series.autocorr(lag=period)
    return {
        "period": period,
        "seasonality_detected": bool(abs(autocorrelation) >= 0.3),
        "autocorrelation_at_period": None if pd.isna(autocorrelation) else float(autocorrelation),
    }


def stationarity_check(series: pd.Series) -> dict:
    clean = series.dropna()
    rolling_mean_change = clean.rolling(max(3, min(12, len(clean) // 4))).mean().dropna()
    variance_ratio = None
    if len(clean) >= 4:
        midpoint = len(clean) // 2
        first_var = clean.iloc[:midpoint].var()
        second_var = clean.iloc[midpoint:].var()
        if first_var and not math.isclose(first_var, 0):
            variance_ratio = float(second_var / first_var)

    result = {
        "method": "rolling statistics",
        "adf_available": STATSMODELS_AVAILABLE,
        "rolling_mean_start": float(rolling_mean_change.iloc[0]) if len(rolling_mean_change) else None,
        "rolling_mean_end": float(rolling_mean_change.iloc[-1]) if len(rolling_mean_change) else None,
        "variance_ratio_second_half_to_first_half": variance_ratio,
    }
    if STATSMODELS_AVAILABLE and len(clean) > 12:
        adf_stat, p_value, used_lag, observations, critical_values, _ = adfuller(clean)
        result.update(
            {
                "method": "Augmented Dickey-Fuller",
                "adf_statistic": float(adf_stat),
                "p_value": float(p_value),
                "used_lag": int(used_lag),
                "observations": int(observations),
                "critical_values": {key: float(value) for key, value in critical_values.items()},
                "is_stationary_at_5_percent": bool(p_value < 0.05),
            }
        )
    return result


def save_plots(series: pd.Series, output_dir: Path, period: int) -> list[str]:
    plot_paths = []
    plot_paths.append(plot_time_series(series, output_dir / "time_series_plot.png"))
    plot_paths.append(plot_rolling(series, output_dir / "trend_rolling_plot.png"))
    plot_paths.append(plot_boxplots(series, output_dir / "monthly_weekly_boxplots.png"))
    plot_paths.append(plot_acf_pacf(series, output_dir / "acf_pacf_plot.png"))

    decomposition_path = output_dir / "decomposition_plot.png"
    if STATSMODELS_AVAILABLE and len(series.dropna()) >= period * 2 and period >= 2:
        decomposition = seasonal_decompose(series.dropna(), model="additive", period=period)
        fig = decomposition.plot()
        fig.set_size_inches(12, 9)
        fig.tight_layout()
        fig.savefig(decomposition_path, dpi=150)
        plt.close(fig)
        plot_paths.append(str(decomposition_path.name))
    return plot_paths


def plot_time_series(series: pd.Series, path: Path) -> str:
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(series.index, series.values, color="#2563eb", linewidth=1.5)
    ax.set_title("Time Series")
    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def plot_rolling(series: pd.Series, path: Path) -> str:
    window = max(3, min(30, len(series) // 10 or 3))
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(series.index, series.values, color="#64748b", alpha=0.5, label="value")
    ax.plot(series.index, series.rolling(window, min_periods=2).mean(), color="#dc2626", label=f"{window}-step rolling mean")
    ax.plot(series.index, series.rolling(window, min_periods=2).std(), color="#16a34a", label=f"{window}-step rolling std")
    ax.set_title("Trend and Rolling Statistics")
    ax.set_xlabel("Timestamp")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def plot_boxplots(series: pd.Series, path: Path) -> str:
    frame = pd.DataFrame({"value": series})
    frame["month"] = frame.index.month
    frame["day_of_week"] = frame.index.day_name()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    frame.boxplot(column="value", by="month", ax=axes[0])
    frame.boxplot(column="value", by="day_of_week", ax=axes[1], rot=45)
    axes[0].set_title("Monthly Boxplot")
    axes[1].set_title("Weekly Boxplot")
    axes[0].set_xlabel("Month")
    axes[1].set_xlabel("Day of Week")
    fig.suptitle("")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def plot_acf_pacf(series: pd.Series, path: Path) -> str:
    clean = series.dropna()
    max_lags = max(1, min(40, len(clean) // 2 - 1))
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    if STATSMODELS_AVAILABLE and max_lags >= 1:
        plot_acf(clean, lags=max_lags, ax=axes[0])
        plot_pacf(clean, lags=max_lags, ax=axes[1], method="ywm")
    else:
        lags = list(range(1, max_lags + 1))
        acf_values = [clean.autocorr(lag=lag) for lag in lags]
        pacf_values = approximate_pacf(clean, lags)
        axes[0].bar(lags, acf_values, color="#2563eb")
        axes[1].bar(lags, pacf_values, color="#7c3aed")
        axes[0].set_title("ACF")
        axes[1].set_title("Approximate PACF")
        for ax in axes:
            ax.axhline(0, color="black", linewidth=0.8)
            ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path.name


def approximate_pacf(series: pd.Series, lags: Iterable[int]) -> list[float]:
    values = []
    clean = series.dropna()
    for lag in lags:
        lagged = pd.concat(
            {"current": clean, "lag": clean.shift(lag)}, axis=1
        ).dropna()
        values.append(float(lagged["current"].corr(lagged["lag"])) if len(lagged) > 1 else 0.0)
    return values


def write_outputs(
    config: TimeSeriesConfig,
    df: pd.DataFrame,
    processed: pd.DataFrame,
    features: pd.DataFrame,
    series: pd.Series,
    value_col: str,
    continuity: dict,
    period: int,
    plot_paths: list[str],
) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    features.to_csv(OUTPUT_DIR / "feature_engineered_dataset.csv")
    processed.to_csv(OUTPUT_DIR / "cleaned_time_series.csv")

    outliers = detect_outliers(series)
    outliers.to_csv(OUTPUT_DIR / "outliers.csv", index=False)

    report = {
        "dataset": str(config.data_path),
        "rows_loaded": int(len(df)),
        "columns_loaded": list(df.columns),
        "selected_timestamp_column": processed.index.name,
        "selected_value_column": value_col,
        "feature_engineering_columns": list(features.columns),
        "continuity_and_missing_values": continuity,
        "trend": trend_summary(series),
        "seasonality": seasonality_summary(series, period),
        "stationarity": stationarity_check(series),
        "outlier_count": int(len(outliers)),
        "plots": plot_paths,
    }
    (OUTPUT_DIR / "eda_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "eda_report.md").write_text(build_markdown_report(report), encoding="utf-8")


def build_markdown_report(report: dict) -> str:
    lines = [
        "# Time Series EDA Report",
        "",
        f"- Dataset: `{report['dataset']}`",
        f"- Rows loaded: {report['rows_loaded']}",
        f"- Timestamp column: `{report['selected_timestamp_column']}`",
        f"- Target column: `{report['selected_value_column']}`",
        "",
        "## Feature Engineering Columns",
        "",
        ", ".join(f"`{column}`" for column in report["feature_engineering_columns"]),
        "",
        "## Continuity and Missing Values",
        "",
        json.dumps(report["continuity_and_missing_values"], indent=2),
        "",
        "## Trend",
        "",
        json.dumps(report["trend"], indent=2),
        "",
        "## Seasonality",
        "",
        json.dumps(report["seasonality"], indent=2),
        "",
        "## Stationarity",
        "",
        json.dumps(report["stationarity"], indent=2),
        "",
        "## Outliers",
        "",
        f"Detected outliers: {report['outlier_count']}",
        "",
        "## Generated Plots",
        "",
    ]
    lines.extend(f"- `{plot}`" for plot in report["plots"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    config = parse_args()
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = load_data(config.data_path)
    timestamp_col = infer_timestamp_column(df, config.timestamp_col)
    value_col = infer_value_column(df, timestamp_col, config.value_col)
    processed, series, continuity = prepare_series(df, timestamp_col, value_col, config.frequency)
    processed.index.name = timestamp_col

    period = estimate_period(series, continuity.get("frequency"), config.period)
    features = create_feature_engineering_columns(series)
    plot_paths = save_plots(series, OUTPUT_DIR, period)

    processed_for_output = processed.rename(columns={value_col: "original_value", f"{value_col}_filled": "value"})
    write_outputs(
        config,
        df,
        processed_for_output,
        features,
        series,
        value_col,
        continuity,
        period,
        plot_paths,
    )

    print("Time-series EDA complete.")
    print(f"Dataset: {config.data_path}")
    print(f"Timestamp column: {timestamp_col}")
    print(f"Target column: {value_col}")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Statsmodels available: {STATSMODELS_AVAILABLE}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
