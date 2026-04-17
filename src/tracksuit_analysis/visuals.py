from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .io import data_path

sns.set_theme(style="whitegrid", context="talk")


def generate_figures(
    panel: pd.DataFrame,
    correlations: pd.DataFrame,
    shortlist: pd.DataFrame,
    trends_merged: pd.DataFrame | None = None,
    reddit_aggregated: pd.DataFrame | None = None,
    output_dir: Path | None = None,
) -> list[Path]:
    destination = output_dir or data_path("figures")
    destination.mkdir(parents=True, exist_ok=True)

    created: list[Path] = [
        plot_funnel_correlation_overview(correlations, destination / "funnel_correlation_overview.png"),
        plot_triangulation_shortlist(shortlist.head(12), destination / "triangulation_shortlist.png"),
        plot_category_timeseries(panel, "Liquor Retailer", destination / "liquor_retailer_consideration_timeseries.png"),
        plot_category_timeseries(panel, "Household Cleaners (Indoor)", destination / "household_cleaners_consideration_timeseries.png"),
    ]
    if trends_merged is not None and not trends_merged.empty:
        created.append(
            plot_trends_alignment_summary(
                trends_merged,
                destination / "trends_vs_survey_alignment.png",
            )
        )
    if reddit_aggregated is not None and not reddit_aggregated.empty:
        created.append(
            plot_reddit_signal_summary(
                reddit_aggregated,
                destination / "reddit_signal_summary.png",
            )
        )
    return created


def plot_funnel_correlation_overview(correlations: pd.DataFrame, output_path: Path) -> Path:
    plot_df = correlations.copy().sort_values("share_consideration_vs_share_awareness", ascending=False)
    top = plot_df.head(10)
    bottom = plot_df.tail(10)
    combined = pd.concat([top, bottom], ignore_index=True).drop_duplicates("category_name")

    fig, ax = plt.subplots(figsize=(14, 9))
    sns.barplot(
        data=combined,
        y="category_name",
        x="share_consideration_vs_share_awareness",
        palette=["#1b9e77" if value >= combined["share_consideration_vs_share_awareness"].median() else "#d95f02" for value in combined["share_consideration_vs_share_awareness"]],
        ax=ax,
    )
    ax.set_title("Share-of-Funnel Alignment by Category")
    ax.set_xlabel("Correlation: Share of Consideration vs Share of Awareness")
    ax.set_ylabel("")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_triangulation_shortlist(shortlist: pd.DataFrame, output_path: Path) -> Path:
    plot_df = shortlist.copy()
    plot_df["label"] = plot_df["category_name"]

    fig, ax = plt.subplots(figsize=(14, 9))
    scatter = ax.scatter(
        plot_df["month_count"],
        plot_df["brand_count"],
        s=plot_df["latest_consideration_spread"].fillna(0.05) * 1600,
        c=plot_df["avg_awareness_to_consideration"],
        cmap="viridis",
        alpha=0.85,
    )
    for _, row in plot_df.iterrows():
        ax.text(row["month_count"] + 0.2, row["brand_count"] + 0.05, row["label"], fontsize=10)

    ax.set_title("Categories Best Suited for Search/Social Triangulation")
    ax.set_xlabel("Months of Survey History")
    ax.set_ylabel("Brands in Category")
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Average Awareness to Consideration Conversion")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_category_timeseries(panel: pd.DataFrame, category_name: str, output_path: Path) -> Path:
    subset = panel.loc[panel["category_name"] == category_name].copy()
    top_brands = (
        subset.groupby("brand_name")["consideration"]
        .mean()
        .sort_values(ascending=False)
        .head(5)
        .index
    )
    subset = subset.loc[subset["brand_name"].isin(top_brands)]

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.lineplot(
        data=subset,
        x="wave_date",
        y="consideration",
        hue="brand_name",
        linewidth=2.5,
        ax=ax,
    )
    ax.set_title(f"Consideration Trends in {category_name}")
    ax.set_xlabel("")
    ax.set_ylabel("Consideration")
    ax.legend(title="Brand", bbox_to_anchor=(1.02, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_trends_alignment_summary(trends_merged: pd.DataFrame, output_path: Path) -> Path:
    rows = []
    for category_name, group in trends_merged.groupby("category_name"):
        corr = group[
            ["share_of_search", "share_of_consideration", "share_of_prompted_awareness", "share_of_preference"]
        ].corr()
        rows.extend(
            [
                {
                    "category_name": category_name,
                    "metric": "Search vs Share of Consideration",
                    "correlation": corr.loc["share_of_search", "share_of_consideration"],
                },
                {
                    "category_name": category_name,
                    "metric": "Search vs Share of Awareness",
                    "correlation": corr.loc["share_of_search", "share_of_prompted_awareness"],
                },
                {
                    "category_name": category_name,
                    "metric": "Search vs Share of Preference",
                    "correlation": corr.loc["share_of_search", "share_of_preference"],
                },
            ]
        )

    plot_df = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(
        data=plot_df,
        x="category_name",
        y="correlation",
        hue="metric",
        palette=["#1b9e77", "#4c78a8", "#d95f02"],
        ax=ax,
    )
    ax.axhline(0, color="black", linewidth=1, linestyle="--")
    ax.set_title("Google Trends Alignment with Survey Share Metrics")
    ax.set_xlabel("")
    ax.set_ylabel("Correlation")
    ax.tick_params(axis="x", rotation=15)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_reddit_signal_summary(reddit_aggregated: pd.DataFrame, output_path: Path) -> Path:
    plot_df = (
        reddit_aggregated.groupby("category_name")[
            [
                "intent_matches",
                "salience_matches",
                "emotion_positive_matches",
                "emotion_negative_matches",
                "controversy_matches",
            ]
        ]
        .sum()
        .reset_index()
        .melt(id_vars="category_name", var_name="signal_type", value_name="matches")
    )

    label_map = {
        "intent_matches": "Intent",
        "salience_matches": "Salience",
        "emotion_positive_matches": "Positive Affect",
        "emotion_negative_matches": "Negative Affect",
        "controversy_matches": "Controversy",
    }
    plot_df["signal_type"] = plot_df["signal_type"].map(label_map)

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.barplot(
        data=plot_df,
        x="category_name",
        y="matches",
        hue="signal_type",
        palette=["#1b9e77", "#4c78a8", "#e6ab02", "#d95f02", "#7570b3"],
        ax=ax,
    )
    ax.set_title("Reddit Pilot Signal Mix by Category")
    ax.set_xlabel("")
    ax.set_ylabel("Total Lexicon Matches")
    ax.tick_params(axis="x", rotation=15)
    ax.legend(title="")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return output_path
