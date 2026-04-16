"""
preprocessing.py
----------------
Merges Tracksuit brand-health survey data with Google Trends / Share of Search data.

Key design choices:
- We join on (category_name, brand_name, wave_date/date) at monthly granularity.
- Trends data uses search_term keys; we reverse-map those to Tracksuit brand_names
  using the BRAND_SEARCH_TERM_OVERRIDES dictionary from data_collection.py.
- Only CONSIDERATION is used as the primary outcome (per the task hint: "search is
  often used as a proxy metric for consideration"). Awareness and preference are
  retained as secondary outcomes.
- We keep only brand × month observations that exist in BOTH datasets, so all
  downstream analysis is on complete cases.
"""

import pandas as pd
from pathlib import Path
from data_collection import BRAND_SEARCH_TERM_OVERRIDES, CATEGORY_CONFIG


def load_tracksuit(path: str | Path = "sample-category-data.csv") -> pd.DataFrame:
    """Load and lightly clean the Tracksuit sample data."""
    df = pd.read_csv(path)
    df.columns = df.columns.str.lower()
    df["wave_date"] = pd.to_datetime(df["wave_date"])
    # Standardise metric names
    df["std_question"] = df["std_question"].str.upper()
    return df


def load_trends(path: str | Path = "data/raw/all_trends.csv") -> pd.DataFrame:
    """Load pre-collected Google Trends data."""
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def map_search_terms_to_brands(df_trends: pd.DataFrame) -> pd.DataFrame:
    """
    Map search_term back to Tracksuit brand_name using the override dict.
    If no mapping exists, search_term == brand_name.
    """
    # Build reverse: search_term → tracksuit brand name
    reverse = {v: k for k, v in BRAND_SEARCH_TERM_OVERRIDES.items()}
    df_trends = df_trends.copy()
    df_trends["brand_name"] = df_trends["search_term"].map(
        lambda t: reverse.get(t, t)  # fall back to search_term itself
    )
    return df_trends


def pivot_tracksuit(df_ts: pd.DataFrame, categories: list[str]) -> pd.DataFrame:
    """
    Pivot Tracksuit data so each metric becomes a column.
    Filters to the specified categories.
    """
    df_ts = df_ts[df_ts["category_name"].isin(categories)].copy()
    df_wide = df_ts.pivot_table(
        index=["category_name", "brand_name", "wave_date"],
        columns="std_question",
        values="percentage_1",
        aggfunc="mean",
    ).reset_index()
    df_wide.columns.name = None
    df_wide.rename(columns={
        "PROMPTED_AWARENESS": "awareness",
        "CONSIDERATION":      "consideration",
        "PREFERENCE":         "preference",
        "wave_date":          "date",
    }, inplace=True)
    return df_wide


def merge_datasets(df_ts_wide: pd.DataFrame, df_trends: pd.DataFrame) -> pd.DataFrame:
    """
    Inner-join Tracksuit and Trends data on (category_name, brand_name, date).
    Both datasets must be at monthly granularity with date as a period start.
    """
    df_trends_mapped = map_search_terms_to_brands(df_trends)

    # Normalise date to month-start in both
    df_ts_wide = df_ts_wide.copy()
    df_ts_wide["date"] = df_ts_wide["date"].dt.to_period("M").dt.to_timestamp()

    df_trends_mapped = df_trends_mapped.copy()
    df_trends_mapped["date"] = df_trends_mapped["date"].dt.to_period("M").dt.to_timestamp()

    merged = pd.merge(
        df_ts_wide,
        df_trends_mapped[["category_name", "brand_name", "date",
                           "index_value", "share_of_search"]],
        on=["category_name", "brand_name", "date"],
        how="inner",
    )
    # Attach intent level
    intent_map = {k: v["intent"] for k, v in CATEGORY_CONFIG.items()}
    merged["intent"] = merged["category_name"].map(intent_map)
    return merged


def add_lagged_sos(df: pd.DataFrame, max_lag: int = 4) -> pd.DataFrame:
    """
    For each brand, add lagged Share of Search columns (sos_lag_1 … sos_lag_N).
    Lag k means: SoS at time t−k predicts brand health at time t.
    (Equivalently: brand health at t correlates with SoS k months earlier.)
    """
    df = df.sort_values(["category_name", "brand_name", "date"])
    for lag in range(1, max_lag + 1):
        df[f"sos_lag_{lag}"] = (
            df.groupby(["category_name", "brand_name"])["share_of_search"]
              .shift(lag)
        )
    return df


def build_analysis_dataset(
    tracksuit_path: str | Path = "sample-category-data.csv",
    trends_path:    str | Path = "data/raw/all_trends.csv",
    max_lag: int = 4,
) -> pd.DataFrame:
    """Full preprocessing pipeline. Returns the merged, lagged dataset."""
    df_ts    = load_tracksuit(tracksuit_path)
    df_trend = load_trends(trends_path)

    categories = list(CATEGORY_CONFIG.keys())
    df_ts_wide = pivot_tracksuit(df_ts, categories)
    merged     = merge_datasets(df_ts_wide, df_trend)
    merged     = add_lagged_sos(merged, max_lag=max_lag)

    print(f"Analysis dataset: {len(merged)} brand-month observations")
    print(f"  Categories:  {merged['category_name'].nunique()}")
    print(f"  Brands:      {merged['brand_name'].nunique()}")
    print(f"  Date range:  {merged['date'].min()} – {merged['date'].max()}")
    print(f"  Missingness: consideration={merged['consideration'].isna().mean():.1%}, "
          f"sos={merged['share_of_search'].isna().mean():.1%}")
    return merged


if __name__ == "__main__":
    df = build_analysis_dataset()
    df.to_csv("data/processed/merged_data.csv", index=False)
    print("Saved → data/processed/merged_data.csv")
