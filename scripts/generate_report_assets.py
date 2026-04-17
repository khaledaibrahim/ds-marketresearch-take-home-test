from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tracksuit_analysis.analysis import run_baseline_analysis
from tracksuit_analysis.visuals import generate_figures


def main() -> None:
    results = run_baseline_analysis()
    processed = ROOT / "data" / "processed"
    trends_merged = None
    reddit_aggregated = None
    trends_path = processed / "survey_trends_merged.csv"
    reddit_path = processed / "reddit_pilot_template_aggregated.csv"
    if trends_path.exists():
        trends_merged = pd.read_csv(trends_path)
    if reddit_path.exists():
        reddit_aggregated = pd.read_csv(reddit_path)

    created = generate_figures(
        panel=results["panel"],
        correlations=results["correlations"],
        shortlist=results["triangulation_shortlist"],
        trends_merged=trends_merged,
        reddit_aggregated=reddit_aggregated,
    )
    print("Created figures:")
    for path in created:
        print(path)


if __name__ == "__main__":
    main()
