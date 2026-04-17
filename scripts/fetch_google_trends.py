from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tracksuit_analysis.analysis import run_baseline_analysis
from tracksuit_analysis.trends import (
    build_monthly_trends,
    fetch_interest_over_time,
    load_trends_targets,
    merge_trends_with_panel,
    parse_interest_over_time,
    require_api_key,
    save_raw_payload,
)


def main() -> None:
    api_key = require_api_key()
    settings, targets = load_trends_targets()
    baseline = run_baseline_analysis()

    raw_frames: list[pd.DataFrame] = []
    output_dir = ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    for target in targets:
        payload = fetch_interest_over_time(
            queries=target.brands,
            api_key=api_key,
            geo=settings.get("geo", "AU"),
            hl=settings.get("hl", "en"),
            date=settings.get("date", "2021-09-01 2025-03-31"),
        )
        save_raw_payload(payload, target.category_name)
        parsed = parse_interest_over_time(payload, target.category_name)
        if not parsed.empty:
            raw_frames.append(parsed)

    if not raw_frames:
        raise RuntimeError("No Google Trends data returned for configured categories.")

    raw_trends = pd.concat(raw_frames, ignore_index=True)
    monthly_trends = build_monthly_trends(raw_trends)
    merged = merge_trends_with_panel(baseline["panel"], monthly_trends)

    raw_trends.to_csv(output_dir / "google_trends_raw_timeseries.csv", index=False)
    monthly_trends.to_csv(output_dir / "google_trends_monthly.csv", index=False)
    merged.to_csv(output_dir / "survey_trends_merged.csv", index=False)

    print("Google Trends collection complete.")
    print(f"Categories collected: {len(targets)}")
    print(f"Monthly rows: {len(monthly_trends):,}")
    print(f"Merged survey/trends rows: {len(merged):,}")


if __name__ == "__main__":
    main()
