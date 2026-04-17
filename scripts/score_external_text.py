from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tracksuit_analysis.lexicons import load_lexicons, score_text_frame
from tracksuit_analysis.triangulation import aggregate_text_signals


def main() -> None:
    preferred_input = ROOT / "data" / "external" / "reddit_pilot_template.csv"
    fallback_input = ROOT / "data" / "external" / "sample_social_posts.csv"
    input_path = preferred_input if preferred_input.exists() else fallback_input
    stem = input_path.stem
    scored_output = ROOT / "data" / "processed" / f"{stem}_scored.csv"
    aggregate_output = ROOT / "data" / "processed" / f"{stem}_aggregated.csv"

    social_posts = pd.read_csv(input_path)
    scored = score_text_frame(
        social_posts,
        text_column="text",
        lexicons=load_lexicons(),
        category_column="category_name",
    )
    aggregated = aggregate_text_signals(social_posts, scored)

    scored.to_csv(scored_output, index=False)
    aggregated.to_csv(aggregate_output, index=False)

    print(f"Input rows read from: {input_path}")
    print(f"Scored rows written to: {scored_output}")
    print(f"Aggregated rows written to: {aggregate_output}")


if __name__ == "__main__":
    main()
