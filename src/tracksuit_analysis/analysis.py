from __future__ import annotations

from pathlib import Path

import pandas as pd

from .io import data_path, load_survey_data
from .panel import add_share_metrics, build_brand_month_panel, compute_category_benchmarks


def run_baseline_analysis(output_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    destination = output_dir or data_path("data", "processed")
    destination.mkdir(parents=True, exist_ok=True)

    survey = load_survey_data()
    panel = add_share_metrics(build_brand_month_panel(survey))
    category_summary = compute_category_benchmarks(panel)
    correlations = compute_metric_correlations(panel)
    shortlist = identify_extension_categories(category_summary, panel)

    survey.to_csv(destination / "survey_clean.csv", index=False)
    panel.to_csv(destination / "brand_month_panel.csv", index=False)
    category_summary.to_csv(destination / "category_summary.csv", index=False)
    correlations.to_csv(destination / "metric_correlations.csv", index=False)
    shortlist.to_csv(destination / "triangulation_shortlist.csv", index=False)

    return {
        "survey": survey,
        "panel": panel,
        "category_summary": category_summary,
        "correlations": correlations,
        "triangulation_shortlist": shortlist,
    }


def compute_metric_correlations(panel: pd.DataFrame) -> pd.DataFrame:
    metrics = [
        "prompted_awareness",
        "consideration",
        "preference",
        "share_of_prompted_awareness",
        "share_of_consideration",
        "share_of_preference",
    ]

    grouped = panel.groupby("category_name")
    rows = []
    for category_name, group in grouped:
        numeric = group[metrics].dropna()
        if len(numeric) < 3:
            continue

        corr = numeric.corr()
        rows.append(
            {
                "category_name": category_name,
                "obs": len(group),
                "consideration_vs_awareness": corr.loc["consideration", "prompted_awareness"],
                "preference_vs_consideration": corr.loc["preference", "consideration"],
                "share_consideration_vs_share_awareness": corr.loc[
                    "share_of_consideration", "share_of_prompted_awareness"
                ],
                "share_preference_vs_share_consideration": corr.loc[
                    "share_of_preference", "share_of_consideration"
                ],
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["share_consideration_vs_share_awareness", "obs"],
        ascending=[False, False],
    ).reset_index(drop=True)


def identify_extension_categories(
    category_summary: pd.DataFrame, panel: pd.DataFrame
) -> pd.DataFrame:
    candidates = category_summary.copy()
    candidates["enough_time_depth"] = candidates["month_count"] >= 18
    candidates["enough_brand_depth"] = candidates["brand_count"] >= 8
    candidates["strong_funnel_signal"] = (
        candidates["avg_awareness_to_consideration"].between(0.2, 0.8)
    )
    candidates["triangulation_ready"] = (
        candidates["enough_time_depth"]
        & candidates["enough_brand_depth"]
        & candidates["strong_funnel_signal"]
    )

    latest = panel["wave_date"].max()
    latest_panel = panel.loc[panel["wave_date"] == latest]
    latest_rank = latest_panel.groupby("category_name")["consideration"].std().rename(
        "latest_consideration_spread"
    )
    candidates = candidates.merge(latest_rank, on="category_name", how="left")

    return candidates.sort_values(
        ["triangulation_ready", "latest_consideration_spread", "brand_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
