"""
data_collection.py
------------------
Collects Google Trends data via SERPApi for selected Australian brand categories.

Design decisions:
- Caches every API response as JSON so the study is fully reproducible without
  re-spending API quota.
- Handles categories with >5 brands via an "anchor brand" normalization: one
  brand is included in every batch, and its index ratio is used to rescale
  subsequent batches onto the same scale.
- Brand name overrides handle ambiguous queries (e.g. "Emma" → "Emma Sleep").
"""

import os
import json
import time
import requests
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration: categories, brands, and search term overrides
# ---------------------------------------------------------------------------

# The five categories we analyse, spanning a range of purchase-intent levels.
# Intent level is our primary hypothesis variable (high-intent categories
# should show a stronger search↔brand-health relationship).
CATEGORY_CONFIG = {
    "Mattresses, beds, and pillows": {
        "intent": "high",
        "brands": [
            "Koala", "Ecosa", "Emma Sleep", "Sleeping Duck", "Ikea",
            "SleepMaker", "Snooze", "Sleepyhead", "Eva mattress", "Noa Home",
        ],
        # Anchor brand must be in every batch for normalization
        "anchor": "Koala",
    },
    "Car Insurance": {
        "intent": "high",
        "brands": [
            "AAMI", "Budget Direct", "NRMA", "Suncorp", "Youi",
            "Bingle", "RACQ", "Huddle", "Rollin Insurance", "Koba Insurance",
        ],
        "anchor": "AAMI",
    },
    "Fast Food": {
        "intent": "moderate",
        "brands": [
            "KFC", "McDonalds", "Subway", "Hungry Jacks", "Guzman y Gomez",
            "Red Rooster", "Oporto", "Grilld", "Mad Mex",
            "Taco Bell", "Zambrero", "Schnitz", "FISHBOWL", "Soul Origin", "Rolld",
        ],
        "anchor": "KFC",
    },
    "Chocolate": {
        "intent": "low",
        "brands": [
            "Cadbury", "Lindt", "Darrell Lea", "Ferrero", "Nestle chocolate",
            "Tony Chocolonely", "Whittakers chocolate",
        ],
        "anchor": "Cadbury",
    },
    "Department Stores": {
        "intent": "moderate",
        "brands": [
            "Kmart Australia", "Big W", "Target Australia", "Myer", "David Jones",
            "Salvos Stores",
        ],
        "anchor": "Kmart Australia",
    },
}

# Map from Tracksuit brand_name → Google Trends search term
BRAND_SEARCH_TERM_OVERRIDES = {
    "Emma":              "Emma Sleep",
    "Eva":               "Eva mattress",
    "Noa":               "Noa Home",
    "ROLLiN' Insurance": "Rollin Insurance",
    "Koba":              "Koba Insurance",
    "Nestlé":            "Nestle chocolate",
    "Tony's Chocolonely":"Tony Chocolonely",
    "Whittaker's":       "Whittakers chocolate",
    "McDonalds":         "McDonalds",
    "Hungry Jack's":     "Hungry Jacks",
    "Grill'd":           "Grilld",
    "Roll'd":            "Rolld",
    "Kmart":             "Kmart Australia",
    "Target":            "Target Australia",
}

# Reverse lookup: search term → Tracksuit brand name (for merging later)
SEARCH_TERM_TO_BRAND = {v: k for k, v in BRAND_SEARCH_TERM_OVERRIDES.items()}
# Add identity mappings for brands not in overrides
for cat_cfg in CATEGORY_CONFIG.values():
    for b in cat_cfg["brands"]:
        if b not in SEARCH_TERM_TO_BRAND:
            SEARCH_TERM_TO_BRAND[b] = b

# ---------------------------------------------------------------------------
# Core API function
# ---------------------------------------------------------------------------

def fetch_trends_batch(keywords: list[str], geo: str, start_date: str, end_date: str,
                       api_key: str, cache_dir: Path) -> pd.DataFrame:
    """
    Fetch Google Trends TIMESERIES for up to 5 keywords via SERPApi.
    Results are cached to `cache_dir` so subsequent runs don't cost quota.

    Returns a DataFrame with columns: date, search_term, index_value
    """
    assert len(keywords) <= 5, "Google Trends supports at most 5 keywords per call"

    cache_key = "__".join(sorted(keywords)).replace(" ", "_").replace("/", "-")
    cache_path = cache_dir / f"{cache_key}.json"

    if cache_path.exists():
        with open(cache_path) as f:
            raw = json.load(f)
    else:
        params = {
            "engine":    "google_trends",
            "q":         ",".join(keywords),
            "geo":       geo,
            "date":      f"{start_date} {end_date}",
            "data_type": "TIMESERIES",
            "api_key":   api_key,
        }
        resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
        resp.raise_for_status()
        raw = resp.json()
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            json.dump(raw, f, indent=2)
        time.sleep(1.5)  # polite rate-limiting

    # Parse response
    records = []
    for point in raw.get("interest_over_time", {}).get("timeline_data", []):
        # SERPApi date can be "Sep 2021" or "2021-09-01T00:00:00+00:00"
        raw_date = point["date"]
        for val in point["values"]:
            records.append({
                "date":         raw_date,
                "search_term":  val["query"],
                "index_value":  val.get("extracted_value", 0),
            })

    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Normalise date to YYYY-MM-01
    df["date"] = pd.to_datetime(df["date"], format="mixed", utc=True).dt.tz_localize(None)
    df["date"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df


# ---------------------------------------------------------------------------
# Multi-batch collection with anchor-brand normalization
# ---------------------------------------------------------------------------

def collect_category_trends(category_name: str, config: dict, geo: str,
                             start_date: str, end_date: str,
                             api_key: str, cache_dir: Path) -> pd.DataFrame:
    """
    Collect Google Trends for all brands in a category, handling >5 brands
    via anchor-brand normalization.

    The anchor brand appears in every batch. Its value in each batch is used
    to rescale that batch onto the scale of the first batch, so all brands
    end up on a common relative index.
    """
    brands  = config["brands"]
    anchor  = config["anchor"]

    # Split into batches of 5 (anchor always in each batch)
    non_anchor = [b for b in brands if b != anchor]
    batches = [[anchor] + non_anchor[i:i+4] for i in range(0, len(non_anchor), 4)]

    all_dfs = []
    anchor_series_b0 = None  # anchor index from first batch (the reference scale)

    for batch_idx, batch in enumerate(batches):
        df_batch = fetch_trends_batch(
            keywords=batch, geo=geo,
            start_date=start_date, end_date=end_date,
            api_key=api_key, cache_dir=cache_dir
        )
        if df_batch.empty:
            continue

        anchor_in_batch = df_batch[df_batch["search_term"] == anchor].set_index("date")["index_value"]

        if batch_idx == 0:
            # First batch: reference scale
            anchor_series_b0 = anchor_in_batch
            all_dfs.append(df_batch)
        else:
            # Subsequent batches: rescale using anchor ratio
            # ratio = anchor_value_in_b0 / anchor_value_in_batch (per date)
            common_dates = anchor_series_b0.index.intersection(anchor_in_batch.index)
            if len(common_dates) == 0:
                all_dfs.append(df_batch)
                continue

            ratio = (anchor_series_b0.loc[common_dates] /
                     anchor_in_batch.loc[common_dates].replace(0, pd.NA)).dropna()

            # Apply mean ratio (more robust than per-date ratio for sparse months)
            mean_ratio = ratio.mean()
            df_batch = df_batch.copy()
            # Don't re-add the anchor (it's already in the first batch)
            df_batch = df_batch[df_batch["search_term"] != anchor]
            df_batch["index_value"] = df_batch["index_value"] * mean_ratio
            all_dfs.append(df_batch)

    if not all_dfs:
        return pd.DataFrame()

    df_cat = pd.concat(all_dfs, ignore_index=True)
    df_cat["category_name"] = category_name
    return df_cat


# ---------------------------------------------------------------------------
# Compute Share of Search
# ---------------------------------------------------------------------------

def compute_share_of_search(df: pd.DataFrame) -> pd.DataFrame:
    """
    Share of Search = brand_index / sum_of_all_brand_indices in category × month.

    Zero-denominator months are dropped.
    """
    df = df.copy()
    totals = df.groupby(["category_name", "date"])["index_value"].sum().rename("category_total")
    df = df.merge(totals, on=["category_name", "date"])
    df["share_of_search"] = df["index_value"] / df["category_total"].replace(0, pd.NA)
    df = df.dropna(subset=["share_of_search"])
    return df


# ---------------------------------------------------------------------------
# Main collection entry point
# ---------------------------------------------------------------------------

def collect_all_categories(
    api_key: str,
    geo: str = "AU",
    start_date: str = "2021-01-01",
    end_date: str = "2025-04-01",
    cache_dir: Path = Path("data/raw/search_trends"),
) -> pd.DataFrame:
    """Collect and return Google Trends data for all configured categories."""
    all_frames = []
    for cat_name, config in CATEGORY_CONFIG.items():
        print(f"  Collecting: {cat_name} ({config['intent']} intent) ...")
        df = collect_category_trends(
            category_name=cat_name, config=config,
            geo=geo, start_date=start_date, end_date=end_date,
            api_key=api_key, cache_dir=cache_dir,
        )
        if not df.empty:
            all_frames.append(df)
            print(f"    → {len(df)} rows, {df['search_term'].nunique()} brands")

    if not all_frames:
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)
    combined = compute_share_of_search(combined)
    return combined


if __name__ == "__main__":
    api_key = os.environ.get("SERPAPI_KEY") or input("Enter SERPAPI_KEY: ")
    print("Collecting Google Trends data ...")
    df = collect_all_categories(api_key=api_key)
    out = Path("data/raw/all_trends.csv")
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows → {out}")
