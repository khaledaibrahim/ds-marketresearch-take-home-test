from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = ROOT / "sample-category-data.csv"


def project_root() -> Path:
    return ROOT


def data_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)


def load_survey_data(path: Path | None = None) -> pd.DataFrame:
    source = path or RAW_DATA_PATH
    df = pd.read_csv(source)
    df = df.rename(columns=str.lower)
    df["wave_date"] = pd.to_datetime(df["wave_date"])

    for column in ["weight_1", "base_weight_1", "percentage_1"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    text_columns = [
        "category_name",
        "geography_name",
        "brand_name",
        "std_question",
    ]
    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    return df.sort_values(["category_name", "brand_name", "wave_date", "std_question"])
