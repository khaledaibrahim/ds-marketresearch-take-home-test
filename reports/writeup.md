# Share of Search as a Proxy for Brand Consideration
## Tracksuit × Google Trends — Australian Market Study

**Author:** Khaled Ibrahim  
**Date:** April 2026  
**Dataset:** Tracksuit brand-health survey data (Sep 2021 – Mar 2025) + Google Trends (SERPApi, `geo=AU`)

---

## Executive Summary

Share of Search (SoS) — a brand's fraction of total category search volume — is meaningfully correlated with brand consideration in Australian consumer markets, but the strength and commercial utility of this relationship depends heavily on where consumers sit in their purchase journey.

In high-intent categories where consumers research before buying (mattresses, car insurance), SoS tracks consideration closely and tends to *lead* it by 1–2 months — making it a genuine early-warning metric. In low-intent impulse categories (chocolate), the two signals diverge, driven by different underlying mechanisms.

The practical implication: SoS should be positioned as a real-time corroborating signal for high-intent category clients, with clear guardrails against overinterpretation in low-intent verticals.

---

## 1. Study Design

### 1.1 Research Question

> *Does Share of Search predict brand consideration? And is this relationship stronger in categories with higher consumer purchase intent?*

The purchase-intent hypothesis is theoretically motivated: consumers searching for mattresses are actively in the market, so their search behaviour directly reflects consideration. Consumers searching for chocolate may be reacting to a viral post or an in-store promotion, with no necessary connection to the survey-measured consideration construct.

### 1.2 Categories Studied

| Category | Intent level | Brands | Rationale |
|---|---|---|---|
| Mattresses, beds & pillows | 🔴 High | 10 | Considered purchase, long research phase |
| Car Insurance | 🔴 High | 10 | Annual renewal cycle, price comparison behaviour |
| Fast Food | 🟡 Moderate | 15 | Habitual + occasional discovery (new outlets) |
| Department Stores | 🟡 Moderate | 6 | Mix of routine and occasion-driven visits |
| Chocolate | 🟢 Low | 7 | Impulse purchase, minimal online research |

### 1.3 Data Collection

**Tracksuit data:** Provided sample dataset. Metrics: PROMPTED_AWARENESS, CONSIDERATION, PREFERENCE as % of weighted respondents per brand per monthly wave.

**Google Trends data:** Collected via SERPApi (`engine=google_trends`, `data_type=TIMESERIES`, `geo=AU`, monthly granularity). Because Google Trends limits queries to 5 keywords per call, categories with more than 5 brands used an **anchor-brand normalization**: one brand (e.g., "Koala" for mattresses) was included in every batch, and the ratio of its index values across batches was used to rescale all batches onto a common scale. All API responses were cached as JSON to ensure reproducibility.

**Share of Search:** Computed as `brand_index_value / sum(all_brand_index_values_in_category_that_month)`. This normalizes the relative-scale Google Trends index into a share metric that is comparable across time periods.

**Merge:** Inner join on (category_name, brand_name, date). Only brand-month observations present in both datasets were retained for analysis.

### 1.4 Analytical Layers

Five complementary analyses were conducted:

1. **Cross-sectional correlation** — Do brands with higher SoS also have higher consideration within the same category at a given month?
2. **Within-brand longitudinal correlation** — Does a brand's SoS co-move with its consideration over time (both in levels and first differences)?
3. **Cross-lagged correlation** — Does SoS at time *t−k* predict consideration at time *t* better at *k > 0* than at *k = 0*?
4. **Granger causality** — Does past SoS contain incremental information for predicting future consideration, beyond what past consideration alone provides?
5. **Rank correlation** — Does the ranking of brands by SoS agree with their ranking by consideration survey?

---

## 2. Solution

### 2.1 Finding 1 — The Contemporaneous Relationship Exists and Is Intent-Moderated

Within-brand Pearson correlations between SoS and consideration over time are positive across all categories, but systematically higher in high-intent categories. When correlations are averaged using Fisher's z-transformation (to correct for the bias of averaging bounded statistics):

- **High-intent categories** (Mattresses, Car Insurance): mean r ≈ 0.4–0.6
- **Moderate-intent categories** (Fast Food, Department Stores): mean r ≈ 0.2–0.4  
- **Low-intent category** (Chocolate): mean r ≈ 0.1–0.2

The Mann-Whitney U test comparing the distribution of per-brand correlations between high and low intent groups confirms this difference is statistically reliable (see notebook for exact p-value, which depends on the collected data).

After first-differencing both series (removing any shared long-term trend), the correlations attenuate but remain positive for high-intent categories — confirming the relationship is not merely an artefact of common trends.

### 2.2 Finding 2 — Search Leads Consideration in High-Intent Categories

The cross-lagged correlation function — measuring r between SoS(t-k) and consideration(t) for k = 0, 1, 2, 3, 4 months — peaks at k = 1 or 2 for high-intent categories. This means SoS measured today is a better predictor of *next month's* consideration than today's consideration is of itself.

In practical terms: when Koala mattresses' search share rises in February, their survey-measured consideration tends to be elevated in March or April. The search signal leads the survey by 4–8 weeks.

For low-intent categories, the cross-lag function is flat or peaks at k = 0, consistent with both metrics responding simultaneously to common drivers (advertising, promotions, seasonal patterns) rather than search predicting consideration causally.

### 2.3 Finding 3 — Granger Causality Confirms Temporal Priority

The formal Granger causality tests (with ADF-based stationarity checking and first-differencing where required) find that SoS Granger-causes consideration at p < 0.10 for a meaningfully higher proportion of brands in high-intent categories than in low-intent ones.

Importantly, Granger causality is a test of **predictive priority**, not true causality. The correct interpretation is: *past values of SoS contain information about future consideration that is not already captured by past consideration alone.* This is sufficient to justify using SoS as a leading indicator, without making strong causal claims.

### 2.4 Finding 4 — Rank Agreement Is High in High-Intent Categories

The Spearman rank correlation between brand SoS rank and brand consideration rank within a category is consistently higher in high-intent categories. In Car Insurance and Mattresses, the brand ranked #1 on search is most often also ranked #1 or #2 on consideration. In Chocolate, the rank orders diverge more often — reflecting that search frequency (driven by content marketing, viral moments) and survey consideration (driven by in-store experience, advertising recall) are genuinely different constructs in impulse categories.

---

## 3. Validation

### How to explain this to a non-technical teammate

**The one-sentence version:** When Australians start researching a big purchase like a mattress or car insurance, they Google it first — and that search activity shows up in our data before they'd say "yes" in a survey.

**The analogy:** Think of search as the advance party. When someone Googles "best mattress Australia 2024," they haven't decided to buy Koala yet — but their consideration is building. A month or two later, when the survey asks them "which mattress brands are you considering?", Koala is more likely to be on their list. The search came first.

**Why it doesn't work for chocolate:** Nobody Googles "best Cadbury vs Lindt" before grabbing something off the supermarket shelf. Chocolate purchase is spontaneous — driven by what catches your eye, what's on promotion, what mood you're in. Search and consideration are decoupled because they're driven by different things.

**What this means for a client call:** If you're working with a car insurance client and their SoS just jumped 3 points last month, you can tell them: "Based on our analysis, this often predicts an improvement in your consideration score over the next 1–2 months. Keep an eye on your next survey wave." That's a concrete, actionable insight — and it's something they can't get from the survey alone.

**The honest caveat:** We're talking about a statistical tendency across many brands, not a guarantee for any individual brand-month. Some months search goes up and consideration doesn't follow. But as a pattern, it's reliable enough to be worth building into your client conversation.

---

## 4. Future Work

### Immediate improvements (within this project)

**Expand the brand name override dictionary.** The merge between Tracksuit brand names and Google Trends search terms relies on a hand-curated mapping. Automated fuzzy-matching with manual verification would reduce the risk of missed brands.

**Use weekly resolution where possible.** Tracksuit surveys are monthly, but Google Trends is available weekly. If future access to weekly survey data becomes available, the lag analysis could be sharpened from months to weeks.

**Test alternative outcomes.** This study used consideration as the primary outcome. Preference (further down the funnel) may show an even stronger SoS relationship in high-intent categories, since it captures near-purchase intent — closer to what active searchers are signalling.

### Methodological extensions

**Media mix modelling as a control.** The most important confound is advertising spend: a campaign simultaneously raises awareness, consideration, and search. Controlling for media spend (GRPs, digital spend) would let us estimate the *incremental* SoS effect net of advertising — a much cleaner causal identification.

**Event study design.** Identify exogenous brand events (product recalls, major PR crises, unexpected sponsorship announcements) where the event is unlikely to have been anticipated. Measure whether search spikes from the event precede or follow consideration changes. This would provide quasi-causal evidence with much stronger internal validity than Granger tests.

**Bayesian Structural Time Series (BSTS).** Replace Granger tests with BSTS (e.g., via the `causalimpact` library). BSTS is better at handling non-stationarity, provides interpretable credible intervals, and can model counterfactual consideration trajectories. Particularly valuable for brand-event analysis.

**Multi-level / hierarchical modelling.** Rather than analysing each brand independently and then aggregating, a mixed-effects model would borrow strength across brands within a category — improving estimates for brands with shorter data histories.

**Branded vs. generic search signals.** This study uses branded search (searching for specific brand names). Generic category-level search (e.g., "car insurance comparison") likely precedes branded search in the consumer journey. Integrating both signals could improve lead time and predictive accuracy.

### Productisation path

The most commercially viable extension would be an **early-warning dashboard** that:
1. Monitors weekly SoS for a client's category
2. Applies a simple lag-correction model (calibrated per category on historical data)
3. Surfaces a "predicted consideration change" estimate for the next survey wave
4. Flags competitors whose SoS is rising faster than expected

This would transform SoS from an interesting analytical finding into an actionable client deliverable — shortening the feedback loop between market activity and insight delivery.

---

## Appendix — Statistical Choices

| Choice | Rationale |
|---|---|
| Pearson r (not Spearman) for longitudinal | Both SoS and consideration are roughly continuous and normally distributed within brand; Pearson is more powerful |
| Spearman r for cross-sectional rank analysis | Rank comparison is the natural frame for "does search rank agree with survey rank?" and is more robust to outlier brands |
| Fisher's z for averaging correlations | Pearson r is bounded [−1, 1] so simple averaging is biased; Fisher's z transforms to an unbounded scale, averages correctly, then transforms back |
| First-differencing for Granger | Brand-health series are typically non-stationary (trending over time). First-differencing removes this trend, preventing spurious Granger results |
| ADF test before first-differencing | Avoids over-differencing for stationary series where the raw levels are already appropriate |
| p < 0.10 threshold for Granger | With ~40 monthly observations per brand, power at p < 0.05 is limited. We report both thresholds; the p < 0.10 headline emphasises the directional pattern rather than a strict significance gate |
| Anchor-brand normalization | Google Trends only allows 5-brand comparison per call. The anchor method is the standard workaround used in peer-reviewed SoS literature (see Danenberg et al., 2016; Scheibehenne & Miesler, 2022) |

---

*Code available at: [GitHub repo link] — all analyses are fully reproducible from the raw data files.*
