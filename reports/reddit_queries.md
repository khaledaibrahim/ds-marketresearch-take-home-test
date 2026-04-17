# Reddit Query Pack

## Recommended Pilot Categories

- `Household Cleaners (Indoor)`
- `Audio Content`
- `Social Media Platforms`

## Why These Are Best

- `Household Cleaners (Indoor)` produces practical product-use language: smell, mould, residue, disinfecting, safety, and recommendations.
- `Audio Content` produces explicit comparison language: Spotify vs Audible, subscription value, offline listening, ads, and switching.
- `Social Media Platforms` produces rich interpretation language: algorithm frustration, creator choice, privacy concerns, and addictive or entertaining use.

These three categories are better Reddit pilots than categories like confectionery because users naturally discuss them in longer, more descriptive text.

## Collection Tactic

For each category:

1. Search 5 to 8 query phrases from `data/external/reddit_collection_plan.csv`.
2. Collect a balanced sample across:
- positive or recommendation-oriented posts
- comparison or switching posts
- complaints or controversy posts
3. Keep only rows where the brand is explicit in the text or context.
4. Paste each row into `data/external/reddit_pilot_template.csv`.

## Suggested Volume

- 30 to 50 rows per category is enough for a strong pilot
- 10 to 15 rows in each theme bucket is even better:
- recommendation / intent
- usage / salience
- friction / controversy

## Practical Advice

- Prefer comments over titles alone because the language is richer.
- Avoid duplicate posts or meme-heavy threads with little text.
- Add one short note explaining why a row was included if the brand mention is indirect.
