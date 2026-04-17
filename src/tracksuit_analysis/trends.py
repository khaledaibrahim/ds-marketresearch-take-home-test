from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
from typing import Any

import pandas as pd
import requests
import yaml

from .io import data_path, project_root


SERPAPI_ENDPOINT = "https://serpapi.com/search.json"


@dataclass
class TrendsTarget:
    category_name: str
    brands: list[str]
    rationale: str = ""


def load_trends_targets(path: Path | None = None) -> tuple[dict[str, Any], list[TrendsTarget]]:
    source = path or project_root() / "config" / "trends_targets.yml"
    with source.open() as handle:
        payload = yaml.safe_load(handle)

    global_settings = {
        key: value for key, value in payload.items() if key != "categories"
    }
    targets = [
        TrendsTarget(
            category_name=item["category_name"],
            brands=item["brands"],
            rationale=item.get("rationale", ""),
        )
        for item in payload["categories"]
    ]
    return global_settings, targets


def require_api_key() -> str:
    api_key = os.getenv("SERPAPI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY is not set.")
    return api_key


def fetch_interest_over_time(
    queries: list[str],
    *,
    api_key: str,
    geo: str = "AU",
    hl: str = "en",
    date: str = "2021-09-01 2025-03-31",
    tz: int = -720,
) -> dict[str, Any]:
    params = {
        "engine": "google_trends",
        "q": ",".join(queries),
        "geo": geo,
        "hl": hl,
        "date": date,
        "data_type": "TIMESERIES",
        "api_key": api_key,
        "tz": tz,
    }
    response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    return payload


def parse_interest_over_time(
    payload: dict[str, Any],
    category_name: str,
) -> pd.DataFrame:
    timeline = payload.get("interest_over_time", {}).get("timeline_data", [])
    rows: list[dict[str, Any]] = []
    for entry in timeline:
        timestamp = pd.to_datetime(int(entry["timestamp"]), unit="s", utc=True).tz_convert(None)
        for value in entry.get("values", []):
            rows.append(
                {
                    "category_name": category_name,
                    "date": timestamp,
                    "brand_name": value.get("query"),
                    "trend_index": value.get("extracted_value"),
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["trend_index"] = pd.to_numeric(df["trend_index"], errors="coerce")
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


def build_monthly_trends(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    monthly = (
        df.groupby(["category_name", "brand_name", "month"], as_index=False)
        .agg(trend_index=("trend_index", "mean"))
        .sort_values(["category_name", "brand_name", "month"])
    )
    totals = monthly.groupby(["category_name", "month"])["trend_index"].transform("sum")
    monthly["share_of_search"] = monthly["trend_index"] / totals.replace({0: pd.NA})
    return monthly


def merge_trends_with_panel(panel: pd.DataFrame, monthly_trends: pd.DataFrame) -> pd.DataFrame:
    if monthly_trends.empty:
        return pd.DataFrame()

    trends = monthly_trends.rename(columns={"month": "wave_date"})
    merged = panel.merge(
        trends,
        on=["category_name", "brand_name", "wave_date"],
        how="inner",
    )
    return merged.sort_values(["category_name", "brand_name", "wave_date"]).reset_index(drop=True)


def save_raw_payload(payload: dict[str, Any], category_name: str, output_dir: Path | None = None) -> Path:
    destination = output_dir or data_path("data", "external", "raw")
    destination.mkdir(parents=True, exist_ok=True)
    safe_name = category_name.lower().replace(" ", "_").replace("&", "and").replace("(", "").replace(")", "")
    path = destination / f"{safe_name}_google_trends.json"
    with path.open("w") as handle:
        json.dump(payload, handle, indent=2)
    return path
