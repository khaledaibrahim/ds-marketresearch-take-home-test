from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tracksuit_analysis.analysis import run_baseline_analysis
from tracksuit_analysis.lexicons import load_lexicons, score_texts
from tracksuit_analysis.triangulation import (
    build_external_signal_template,
    save_external_signal_template,
)


def main() -> None:
    results = run_baseline_analysis()

    demo_texts = [
        "I keep seeing this brand everywhere and now I am curious to try it.",
        "Best value, compare prices, worth switching for the next purchase.",
        "People are talking about the brand, but the tone feels angry and frustrated.",
    ]
    lexicon_scores = score_texts(demo_texts, load_lexicons())
    lexicon_output = ROOT / "data" / "processed" / "lexicon_demo_scores.csv"
    lexicon_output.parent.mkdir(parents=True, exist_ok=True)
    lexicon_scores.to_csv(lexicon_output, index=False)

    panel = results["panel"]
    shortlist = results["triangulation_shortlist"]
    shortlist_categories = shortlist.loc[shortlist["triangulation_ready"], "category_name"].head(5).tolist()
    template = build_external_signal_template(panel, categories=shortlist_categories, months_back=6)
    template_path = save_external_signal_template(template)

    print("Baseline analysis complete.")
    print(f"Rows in brand-month panel: {len(panel):,}")
    print("Top candidate categories for search/social triangulation:")
    print(shortlist.head(10)[["category_name", "brand_count", "month_count", "triangulation_ready"]].to_string(index=False))
    print(f"External signal template saved to: {template_path}")


if __name__ == "__main__":
    main()
