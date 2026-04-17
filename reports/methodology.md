# Methodology Note

## Why a Lexicon Approach

For this take-home, I chose a lexicon-based text method because it is:

- transparent
- easy to audit
- easy to adapt by category
- realistic as an initial product prototype

This is better suited to a small exploratory pilot than training a black-box model on a tiny labeled sample.

## What Lexicons Are Used

The project uses five interpretable lexicon groups:

- `intent`
- `salience`
- `emotion_positive`
- `emotion_negative`
- `controversy`

The current dictionaries are implemented in `config/lexicons.yml`.

## Relationship to NRC

The emotion framing is inspired by human emotion lexicon work such as the NRC Emotion Lexicon, but the implementation in this take-home is not a strict NRC deployment.

Instead, it is a custom category-aware lexicon system designed for the Tracksuit use case:

- identify active demand or switching intent
- separate ordinary brand salience from strong positive or negative affect
- flag discussion that may be driven by controversy or friction rather than healthy demand

The cleanest way to describe the method is:

- `emotion_positive` and `emotion_negative` are NRC-inspired affect layers
- `intent`, `salience`, and `controversy` are custom business extensions added for brand and market-research interpretation

This is a deliberate design choice, not an omission. A direct NRC-only implementation would be useful for broad emotion tagging, but it would not be enough to distinguish demand, salience, friction, and controversy in brand discussion.

## Why Category Overrides Matter

Generic sentiment words are not enough for this business problem.

Examples:

- `subscription`, `offline`, and `top-up` are highly informative in `Audio Content`
- `mould`, `smell`, `chemical`, and `harsh` matter in `Household Cleaners (Indoor)`
- `algorithm`, `creator`, and `privacy` matter in `Social Media Platforms`

That is why the implementation includes category-specific override dictionaries on top of the shared base lexicons.

## Validity Caveats

- This is a heuristic feature-engineering layer, not a validated psychological instrument.
- It should not be used to infer precise individual emotions.
- It is best used as an interpretation layer on top of survey and search data.
- In production, it should be calibrated against human-labeled samples and reviewed category by category.
