# Tracksuit Take-Home Write-Up

## Research Question

When can search-based signals complement Tracksuit's survey-based brand metrics, and how might a lightweight text layer improve interpretation?

## Proposed Answer

My working hypothesis is that search should be treated as a directional, behavioral proxy for consideration rather than a universal substitute for survey-based brand tracking. Its practical value should increase when:

- the category has enough consumer intent to generate meaningful search volume
- brand choice is explicit enough that search terms map to brands cleanly
- search is interpreted alongside text signals that distinguish healthy interest from controversy or noise

This leads to a more product-relevant recommendation than a pure correlation study: use search to detect movement quickly, then use discourse signals to interpret whether that movement reflects demand, salience, or friction.

## Study Design

1. Reshape the survey data into a brand-month panel with awareness, consideration, and preference.
2. Compute funnel conversion metrics and within-category share metrics.
3. Identify categories where search triangulation is most likely to be informative.
4. Pilot a lexicon layer for text-based signals covering intent, salience, emotion, and controversy.

## Lexicon Method

The text layer is lexicon-based by design: the goal is interpretability and scalability rather than building a fully supervised NLP model for a small take-home sample.

I use five lexicon families:

- `intent`: words and phrases that imply active evaluation or purchase behavior such as `compare`, `switch`, `best`, `review`, and `worth it`
- `salience`: words that indicate brand noticing, familiarity, or visibility such as `know`, `noticed`, `seen`, and `recommend`
- `emotion_positive`: words that signal favorable affect or ease such as `trust`, `love`, `convenient`, and `effective`
- `emotion_negative`: words that capture friction or aversion such as `frustrated`, `harsh`, `smell`, `expensive`, and `toxic`
- `controversy`: words associated with risk, policy, or reputational concern such as `privacy`, `algorithm`, `ban`, `problem`, and `scandal`

Methodologically, this should be described as a hybrid approach:

- the affect layer is inspired by human emotion lexicon work such as the NRC Emotion Lexicon and similar NRC-style emotion categories
- the actual lexicons used in this project are not a direct NRC implementation; they are custom, category-aware dictionaries tuned for the Tracksuit use case
- the custom part is intentional because Tracksuit's decision problem is not generic sentiment detection; it is distinguishing demand, salience, friction, and controversy in brand discussion

In practice, the design is:

- `emotion_positive` and `emotion_negative` are the closest pieces to an NRC-style affect layer
- `intent`, `salience`, and `controversy` are business-specific extensions added to make the method useful for brand tracking and market-research interpretation

The category-specific overrides are important for validity. For example:

- in `Audio Content`, terms like `subscription`, `offline`, and `playlist` are meaningful intent or usage signals
- in `Household Cleaners (Indoor)`, terms like `mould`, `harsh`, `chemical`, and `smell` matter more than generic sentiment words
- in `Social Media Platforms`, terms like `algorithm`, `privacy`, and `creator` help separate platform controversy from simple popularity

This makes the system more explainable and easier to adapt at scale, because the same framework can be extended with category-specific dictionaries across many verticals without retraining a model.

## Early Baseline Read

The initial baseline suggests that some categories have especially strong funnel alignment and enough structure to justify a triangulation pilot. Early candidates include:

- Liquor Retailer
- Garden Care
- Household Cleaners (Indoor)
- Sugar confectionery
- Audio Content

These categories combine enough monthly depth, enough brands, and enough variation in consideration to make external signals more useful.

## Live Trends Read

I collected live Google Trends data for four shortlisted categories and merged it to the survey panel at the brand-month level. The first pass points to a clear category-conditional result:

- `Liquor Retailer` shows strong search alignment with share of consideration
- `Audio Content` also shows a meaningful positive relationship
- `Social Media Platforms` is mixed: search appears somewhat useful, but less cleanly tied to awareness
- `Household Cleaners (Indoor)` performs poorly, suggesting that search is a weak proxy there

In other words, the data supports using search as a complement in categories where brand-level consumer intent is explicit and digitally expressed, but not as a universal substitute for survey data.

## Reddit Pilot Read

I also built a small Reddit pilot with 20 rows per category across:

- `Household Cleaners (Indoor)`
- `Audio Content`
- `Social Media Platforms`

The lexicon-scored pilot adds interpretive value on top of search:

- `Audio Content` is rich in intent and switching language: limits, top-ups, value, substitutions, and workarounds
- `Household Cleaners (Indoor)` is rich in negative-friction language: smell, harshness, chemical concern, and safety trade-offs
- `Social Media Platforms` is strongest in salience and controversy: algorithm frustration, ad load, privacy, and creator uncertainty

This supports the triangulation argument directly: text helps explain whether attention reflects active demand, ordinary salience, or negative attention.

## Validation Principles

- Separate descriptive findings from stronger causal claims.
- Highlight where the relationship is strong, weak, or ambiguous by category.
- Treat social or text-based signals as an interpretation layer unless they clearly improve predictive value.
- Be explicit that the lexicon layer is a transparent heuristic method, not a validated psychological measurement instrument.
- Use lexicons to classify attention into interpretable buckets, not to claim exact emotional states for individuals.
- Treat category-specific lexicon tuning as an operational design choice that improves product usefulness but still requires further validation on larger samples.

## Product Implication

If the final analysis supports the baseline read, I would not recommend replacing surveys with search broadly. I would recommend a tiered product approach:

- use search as a fast directional indicator for consideration-heavy categories
- use text-based lexicons to explain why attention is moving
- keep survey data as the calibration layer for brand health interpretation

## Scalability

This approach is intentionally designed to scale:

- the survey and Trends pieces already operate as structured brand-month panels
- the text layer can be applied to any text source that can be mapped to brand, category, and date
- the lexicon system is modular, so new categories can be supported by adding targeted override dictionaries rather than redesigning the whole pipeline

In a larger production framework, I would evolve this by:

- expanding the lexicons with expert review and category QA
- benchmarking the lexicon features against human-coded samples
- using the lexicon outputs as transparent baseline features before introducing more complex NLP models

## Final Recommendation

My recommendation would be:

1. Do not position Share of Search as a universal replacement for survey-based consideration.
2. Use Share of Search selectively in categories where it empirically aligns with consideration and where brand search intent is naturally high.
3. Add a lightweight text interpretation layer so that spikes in search or discussion can be classified as:
- purchase or switching intent
- general brand salience
- product friction or dissatisfaction
- controversy or platform-level concern
4. Keep survey tracking as the decision anchor, while using search plus text as a cheaper and faster complement between waves.
