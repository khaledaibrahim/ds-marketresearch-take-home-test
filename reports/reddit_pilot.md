# Reddit Pilot Guide

## Goal

Use a small Reddit pilot to test whether text signals help interpret brand movement as:

- active consideration
- general salience
- positive affinity
- negative or controversy-driven attention

## Recommended Pilot Categories

- `Household Cleaners (Indoor)`
- `Audio Content`
- `Social Media Platforms`

These categories are a good fit because people naturally discuss product comparison, subscriptions, complaints, switching, and usage experience in text.

## Data Collection Shape

Use one row per Reddit post or comment in `data/external/reddit_pilot_template.csv`.

Suggested fields:

- subreddit
- post or comment type
- category name
- brand name
- date
- raw text
- URL
- optional notes about why the row was included

## Practical Sampling Rules

- keep the pilot small and high-quality rather than broad
- aim for 30 to 100 rows per category
- prefer brand-explicit posts over vague category chatter
- include both positive and negative discussion so the lexicons can separate intent from friction

## Suggested Search Logic

- `brand` alone
- `brand vs competitor`
- `brand review`
- `brand complaint`
- `category + best`
- `category + recommendation`

For a ready-made starting pack, use `reports/reddit_queries.md` and `data/external/reddit_collection_plan.csv`.

## Scoring Workflow

1. Paste rows into `data/external/reddit_pilot_template.csv`.
2. Run `python3 scripts/score_external_text.py`.
3. Review the scored and aggregated outputs in `data/processed/`.
4. Compare those features to consideration or share-of-consideration in the main analysis.
