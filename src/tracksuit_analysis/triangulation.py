from __future__ import annotations

from pathlib import Path

import pandas as pd

from .io import data_path


EXTERNAL_SIGNAL_COLUMNS = [
    "source",
    "category_name",
    "brand_name",
    "signal_date",
    "signal_type",
    "signal_value",
    "signal_unit",
    "text",
    "url",
    "notes",
]


def build_external_signal_template(
    panel: pd.DataFrame,
    categories: list[str] | None = None,
    months_back: int = 6,
) -> pd.DataFrame:
    latest_date = panel["wave_date"].max()
    filtered = panel.loc[panel["wave_date"] >= latest_date - pd.DateOffset(months=months_back)]

    if categories:
        filtered = filtered.loc[filtered["category_name"].isin(categories)]

    template = (
        filtered[["category_name", "brand_name", "wave_date"]]
        .drop_duplicates()
        .rename(columns={"wave_date": "signal_date"})
        .sort_values(["category_name", "brand_name", "signal_date"])
        .reset_index(drop=True)
    )

    template.insert(0, "source", "")
    template["signal_type"] = ""
    template["signal_value"] = pd.NA
    template["signal_unit"] = ""
    template["text"] = ""
    template["url"] = ""
    template["notes"] = ""

    return template[EXTERNAL_SIGNAL_COLUMNS]


def aggregate_text_signals(
    external_signals: pd.DataFrame,
    text_scores: pd.DataFrame,
) -> pd.DataFrame:
    score_columns = [
        column
        for column in text_scores.columns
        if column not in external_signals.columns and column != "text"
    ]
    joined = pd.concat(
        [
            external_signals.reset_index(drop=True),
            text_scores[score_columns].reset_index(drop=True),
        ],
        axis=1,
    )

    grouped = (
        joined.groupby(["source", "category_name", "brand_name", "signal_date"], dropna=False)
        .agg(
            mention_count=("text", "count"),
            mean_signal_value=("signal_value", "mean"),
            intent_matches=("intent_matches", "sum"),
            salience_matches=("salience_matches", "sum"),
            emotion_positive_matches=("emotion_positive_matches", "sum"),
            emotion_negative_matches=("emotion_negative_matches", "sum"),
            controversy_matches=("controversy_matches", "sum"),
        )
        .reset_index()
    )

    for metric in [
        "intent_matches",
        "salience_matches",
        "emotion_positive_matches",
        "emotion_negative_matches",
        "controversy_matches",
    ]:
        grouped[f"{metric}_per_mention"] = grouped[metric] / grouped["mention_count"].replace(0, pd.NA)

    return grouped


def save_external_signal_template(template: pd.DataFrame, output_path: Path | None = None) -> Path:
    destination = output_path or data_path("data", "external", "external_signal_template.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(destination, index=False)
    return destination
