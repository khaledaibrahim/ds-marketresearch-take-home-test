from __future__ import annotations

import numpy as np
import pandas as pd


QUESTION_MAP = {
    "PROMPTED_AWARENESS": "prompted_awareness",
    "CONSIDERATION": "consideration",
    "PREFERENCE": "preference",
}


def build_brand_month_panel(df: pd.DataFrame) -> pd.DataFrame:
    panel = (
        df.assign(metric_name=df["std_question"].map(QUESTION_MAP))
        .pivot_table(
            index=["category_name", "brand_name", "wave_date"],
            columns="metric_name",
            values="percentage_1",
            aggfunc="mean",
        )
        .reset_index()
    )
    panel.columns.name = None

    panel["awareness_to_consideration"] = _safe_divide(
        panel["consideration"], panel["prompted_awareness"]
    )
    panel["consideration_to_preference"] = _safe_divide(
        panel["preference"], panel["consideration"]
    )
    panel["awareness_to_preference"] = _safe_divide(
        panel["preference"], panel["prompted_awareness"]
    )

    panel["category_month_brand_count"] = panel.groupby(
        ["category_name", "wave_date"]
    )["brand_name"].transform("nunique")

    return panel.sort_values(["category_name", "brand_name", "wave_date"]).reset_index(
        drop=True
    )


def compute_category_benchmarks(panel: pd.DataFrame) -> pd.DataFrame:
    summary = (
        panel.groupby("category_name")
        .agg(
            brand_count=("brand_name", "nunique"),
            month_count=("wave_date", "nunique"),
            avg_awareness=("prompted_awareness", "mean"),
            avg_consideration=("consideration", "mean"),
            avg_preference=("preference", "mean"),
            avg_awareness_to_consideration=("awareness_to_consideration", "mean"),
            avg_consideration_to_preference=("consideration_to_preference", "mean"),
        )
        .reset_index()
    )

    summary["avg_brands_per_month"] = summary["brand_count"]
    summary["consideration_spread"] = (
        panel.groupby("category_name")["consideration"].std().reset_index(drop=True)
    )

    return summary.sort_values(["month_count", "brand_count", "category_name"]).reset_index(
        drop=True
    )


def add_share_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    panel = panel.copy()
    for metric in ["prompted_awareness", "consideration", "preference"]:
        total = panel.groupby(["category_name", "wave_date"])[metric].transform("sum")
        panel[f"share_of_{metric}"] = _safe_divide(panel[metric], total)

    return panel


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace({0: np.nan})
    return numerator / denominator
