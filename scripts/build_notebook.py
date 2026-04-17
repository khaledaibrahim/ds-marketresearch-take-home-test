from __future__ import annotations

from pathlib import Path
import sys

import nbformat as nbf
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    processed = ROOT / "data" / "processed"
    notebook_path = ROOT / "notebooks" / "analysis.ipynb"
    notebook_path.parent.mkdir(parents=True, exist_ok=True)

    correlations = pd.read_csv(processed / "metric_correlations.csv")
    shortlist = pd.read_csv(processed / "triangulation_shortlist.csv")
    trends_merged_path = processed / "survey_trends_merged.csv"
    reddit_scored_path = processed / "reddit_pilot_template_scored.csv"
    reddit_aggregated_path = processed / "reddit_pilot_template_aggregated.csv"
    top_categories = shortlist.head(5)["category_name"].tolist()
    strongest = correlations.head(5)["category_name"].tolist()

    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(
            "# Tracksuit Take-Home Analysis\n\n"
            "This notebook summarizes the baseline survey analysis and the proposed search/social triangulation extension."
        ),
        nbf.v4.new_markdown_cell(
            "## Framing\n\n"
            "Goal: assess whether search-like signals can complement or partially substitute survey-based brand metrics, "
            "and identify where a text layer could improve interpretation."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import pandas as pd\n"
            "\n"
            "ROOT = Path.cwd().resolve().parents[0] if Path.cwd().name == 'notebooks' else Path.cwd().resolve()\n"
            "processed = ROOT / 'data' / 'processed'\n"
            "panel = pd.read_csv(processed / 'brand_month_panel.csv', parse_dates=['wave_date'])\n"
            "correlations = pd.read_csv(processed / 'metric_correlations.csv')\n"
            "shortlist = pd.read_csv(processed / 'triangulation_shortlist.csv')\n"
            "panel.head()"
        ),
        nbf.v4.new_markdown_cell(
            "## Baseline read\n\n"
            "The first pass uses the provided survey data only. It turns the raw file into a brand-month panel with:\n\n"
            "- prompted awareness\n"
            "- consideration\n"
            "- preference\n"
            "- funnel conversion rates\n"
            "- within-category share metrics\n"
        ),
        nbf.v4.new_code_cell(
            "shortlist[['category_name', 'brand_count', 'month_count', 'triangulation_ready']].head(10)"
        ),
        nbf.v4.new_markdown_cell(
            "## Categories that look most promising for triangulation\n\n"
            f"Current shortlist: {', '.join(top_categories)}.\n\n"
            "These categories have enough history, enough brands, and enough spread in consideration to make external signals informative."
        ),
        nbf.v4.new_markdown_cell(
            "## Funnel alignment overview\n\n"
            f"Strongest current share-level alignment categories include: {', '.join(strongest)}."
        ),
        nbf.v4.new_markdown_cell(
            "![Funnel Correlation Overview](../figures/funnel_correlation_overview.png)\n\n"
            "![Triangulation Shortlist](../figures/triangulation_shortlist.png)"
        ),
        nbf.v4.new_markdown_cell(
            "## Example category reads\n\n"
            "The two example time-series plots below show why this should be presented as category-conditional rather than universal."
        ),
        nbf.v4.new_markdown_cell(
            "![Liquor Retailer Consideration](../figures/liquor_retailer_consideration_timeseries.png)\n\n"
            "![Household Cleaners Consideration](../figures/household_cleaners_consideration_timeseries.png)"
        ),
        nbf.v4.new_markdown_cell(
            "## Google Trends merge\n\n"
            "I pulled live Google Trends data for four shortlisted categories and merged it to the survey panel at the brand-month level.\n\n"
            "The most important finding is not that search works everywhere. It is that search works unevenly:\n\n"
            "- stronger in `Liquor Retailer`\n"
            "- meaningfully positive in `Audio Content`\n"
            "- mixed in `Social Media Platforms`\n"
            "- weak in `Household Cleaners (Indoor)`\n\n"
            "That pattern is exactly why a triangulation story is stronger than a one-metric replacement story."
        ),
        nbf.v4.new_code_cell(
            "trends_merged = processed / 'survey_trends_merged.csv'\n"
            "if trends_merged.exists():\n"
            "    merged = pd.read_csv(trends_merged)\n"
            "    rows = []\n"
            "    for category_name, group in merged.groupby('category_name'):\n"
            "        corr = group[['share_of_search','share_of_consideration','share_of_prompted_awareness','share_of_preference']].corr()\n"
            "        rows.append({\n"
            "            'category_name': category_name,\n"
            "            'search_vs_share_consideration': corr.loc['share_of_search', 'share_of_consideration'],\n"
            "            'search_vs_share_awareness': corr.loc['share_of_search', 'share_of_prompted_awareness'],\n"
            "            'search_vs_share_preference': corr.loc['share_of_search', 'share_of_preference'],\n"
            "        })\n"
            "    display(pd.DataFrame(rows).sort_values('search_vs_share_consideration', ascending=False))\n"
            "else:\n"
            "    print('Run python3 scripts/fetch_google_trends.py after setting SERPAPI_API_KEY')"
        ),
        nbf.v4.new_markdown_cell(
            "## Text and lexicon extension\n\n"
            "The next layer is not intended to replace survey metrics directly. Instead, it helps interpret whether movement in search or mentions looks like:\n\n"
            "- healthy demand and active consideration\n"
            "- brand salience without clear purchase intent\n"
            "- controversy or complaint-driven attention\n"
        ),
        nbf.v4.new_code_cell(
            "pd.read_csv(processed / 'sample_social_posts_scored.csv').head()"
        ),
        nbf.v4.new_markdown_cell(
            "## Reddit pilot setup\n\n"
            "For a lightweight Reddit pilot, I would prioritize three categories where text discussion is likely to be rich and decision-relevant:\n\n"
            "- Household Cleaners (Indoor)\n"
            "- Audio Content\n"
            "- Social Media Platforms\n\n"
            "The lexicon is category-aware, so terms like `mould`, `subscription`, `algorithm`, and `privacy` are only emphasized where they make sense."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "reddit_scored = processed / 'reddit_pilot_template_scored.csv'\n"
            "reddit_agg = processed / 'reddit_pilot_template_aggregated.csv'\n"
            "if reddit_scored.exists() and reddit_agg.exists():\n"
            "    display(pd.read_csv(reddit_scored).head())\n"
            "    display(pd.read_csv(reddit_agg).head())\n"
            "else:\n"
            "    print('Run python3 scripts/score_external_text.py after filling data/external/reddit_pilot_template.csv')"
        ),
        nbf.v4.new_markdown_cell(
            "## How I would use the Reddit pilot\n\n"
            "I would not treat Reddit volume as a direct replacement for consideration. Instead, I would use it to explain whether a spike in search or salience is being driven by:\n\n"
            "- shopping or switching intent\n"
            "- product usage conversation\n"
            "- complaints or controversy\n"
            "- creator or platform buzz\n"
        ),
        nbf.v4.new_markdown_cell(
            "## Recommendation direction\n\n"
            "My current recommendation would be to position search as a fast directional signal for consideration in categories where it empirically aligns, then pair it with a lightweight discourse layer before making stronger brand-health claims. Survey data should remain the calibration anchor."
        ),
    ]

    with notebook_path.open("w") as handle:
        nbf.write(nb, handle)

    print(f"Notebook written to: {notebook_path}")


if __name__ == "__main__":
    main()
