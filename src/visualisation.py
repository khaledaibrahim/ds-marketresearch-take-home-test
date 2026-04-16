"""
visualisation.py
----------------
All plots for the study. Designed to be readable by non-technical audiences
(clear labels, plain-English titles, minimal jargon in axis labels).

Tracksuit brand colour palette is used where appropriate.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from pathlib import Path

# ---------------------------------------------------------------------------
# Tracksuit-inspired colour palette
# ---------------------------------------------------------------------------
COLOURS = {
    "high":     "#FF6B6B",   # coral / warm red  → high intent
    "moderate": "#4ECDC4",   # teal               → moderate intent
    "low":      "#95A5A6",   # muted grey-green   → low intent
    "primary":  "#2C3E50",   # dark navy          → generic
    "accent":   "#F39C12",   # amber
    "light":    "#ECF0F1",   # near-white bg
}
INTENT_ORDER = ["high", "moderate", "low"]
INTENT_LABELS = {"high": "High-intent", "moderate": "Moderate-intent", "low": "Low-intent"}

plt.rcParams.update({
    "font.family":        "sans-serif",
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.labelsize":     11,
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "figure.dpi":         130,
    "figure.facecolor":   "white",
})

OUT_DIR = Path("reports/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def _save(name: str):
    plt.tight_layout()
    plt.savefig(OUT_DIR / f"{name}.png", bbox_inches="tight", dpi=150)
    plt.close()


# ---------------------------------------------------------------------------
# Plot 1: Time series overlay (SoS vs Consideration) for select brands
# ---------------------------------------------------------------------------

def plot_timeseries_examples(df: pd.DataFrame,
                             examples: list[tuple[str, str]]) -> None:
    """
    Plot SoS vs Consideration over time for a curated list of (category, brand) pairs.
    Shows dual y-axes so both metrics are visible despite different scales.
    """
    n = len(examples)
    fig, axes = plt.subplots(n, 1, figsize=(12, 3.8 * n), sharex=False)
    if n == 1:
        axes = [axes]

    for ax, (cat, brand) in zip(axes, examples):
        sub = df[(df["category_name"] == cat) & (df["brand_name"] == brand)].sort_values("date")
        if sub.empty:
            ax.set_title(f"{brand} ({cat}) – no data")
            continue

        ax2 = ax.twinx()
        l1, = ax.plot(sub["date"], sub["share_of_search"] * 100,
                      color=COLOURS["accent"], linewidth=2, label="Share of Search (%)")
        l2, = ax2.plot(sub["date"], sub["consideration"] * 100,
                       color=COLOURS["primary"], linewidth=2, linestyle="--",
                       label="Consideration (%)")

        ax.set_ylabel("Share of Search (%)", color=COLOURS["accent"])
        ax2.set_ylabel("Consideration (%)", color=COLOURS["primary"])
        ax.tick_params(axis="y", labelcolor=COLOURS["accent"])
        ax2.tick_params(axis="y", labelcolor=COLOURS["primary"])
        ax.set_title(f"{brand}  ·  {cat}")
        ax.set_xlabel("")

        lines = [l1, l2]
        ax.legend(lines, [l.get_label() for l in lines], loc="upper left", fontsize=9)

    fig.suptitle("Share of Search vs Consideration — selected brands",
                 fontsize=14, fontweight="bold", y=1.01)
    _save("01_timeseries_examples")


# ---------------------------------------------------------------------------
# Plot 2: Cross-sectional scatter (SoS vs Consideration, all brands × months)
# ---------------------------------------------------------------------------

def plot_cross_sectional_scatter(df: pd.DataFrame,
                                 outcome: str = "consideration") -> None:
    """One scatter point per (brand, month), coloured by intent level."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
    intent_groups = [("high", "High-intent categories"),
                     ("moderate", "Moderate-intent"),
                     ("low", "Low-intent categories")]

    for ax, (intent, title) in zip(axes, intent_groups):
        sub = df[df["intent"] == intent].dropna(subset=["share_of_search", outcome])
        if sub.empty:
            continue
        ax.scatter(sub["share_of_search"] * 100, sub[outcome] * 100,
                   alpha=0.35, s=18, color=COLOURS[intent], edgecolors="none")
        # OLS trend line
        x = sub["share_of_search"].values
        y = sub[outcome].values
        m, b = np.polyfit(x, y, 1)
        xr = np.linspace(x.min(), x.max(), 100)
        ax.plot(xr * 100, (m * xr + b) * 100, color="black", linewidth=1.5)

        from scipy.stats import pearsonr
        r, p = pearsonr(x, y)
        ax.set_title(f"{title}\nr = {r:.2f}  (p {'< 0.001' if p < 0.001 else f'= {p:.3f}'})",
                     fontsize=11)
        ax.set_xlabel("Share of Search (%)")
        ax.set_ylabel(f"{outcome.capitalize()} (%)" if ax == axes[0] else "")

    fig.suptitle("Share of Search vs Brand Consideration — by purchase-intent level",
                 fontsize=13, fontweight="bold")
    _save("02_cross_sectional_scatter")


# ---------------------------------------------------------------------------
# Plot 3: Cross-lagged correlation function
# ---------------------------------------------------------------------------

def plot_cross_lag(df_lag: pd.DataFrame) -> None:
    """
    Bar chart showing mean r between SoS(t-k) and Consideration(t)
    for k = 0, 1, 2, 3, 4 months, by intent level.
    """
    intent_order = [i for i in INTENT_ORDER if i in df_lag["intent"].unique()]
    n_intent = len(intent_order)
    fig, axes = plt.subplots(1, n_intent, figsize=(5 * n_intent, 5), sharey=True)
    if n_intent == 1:
        axes = [axes]

    for ax, intent in zip(axes, intent_order):
        sub = df_lag[df_lag["intent"] == intent].sort_values("lag")
        cats = sub["category_name"].unique()
        x = np.arange(sub["lag"].max() + 1)
        width = 0.8 / len(cats)

        for i, cat in enumerate(cats):
            cat_data = sub[sub["category_name"] == cat].set_index("lag")["mean_r"]
            cat_vals = [cat_data.get(lag, np.nan) for lag in x]
            bars = ax.bar(x + i * width, cat_vals, width=width, label=cat, alpha=0.8)

        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
        ax.set_xlabel("Lag (months)")
        ax.set_title(f"{INTENT_LABELS[intent]}", color=COLOURS[intent])
        ax.set_xticks(x + width * (len(cats) - 1) / 2)
        ax.set_xticklabels([f"t-{k}" if k > 0 else "t (same month)" for k in x])
        if ax == axes[0]:
            ax.set_ylabel("Mean Pearson r (SoS → Consideration)")
        ax.legend(fontsize=7, loc="upper right")

    fig.suptitle("Does Search Lead Brand Consideration?\nCross-lagged correlation by intent level",
                 fontsize=13, fontweight="bold")
    _save("03_cross_lag_correlation")


# ---------------------------------------------------------------------------
# Plot 4: Granger causality summary heatmap
# ---------------------------------------------------------------------------

def plot_granger_summary(df_granger: pd.DataFrame) -> None:
    """Bubble chart: % of brands where SoS Granger-causes consideration."""
    df_agg = (df_granger.groupby(["category_name", "intent"])
                         .agg(n=("brand_name", "count"),
                              pct_sig=("significant_0.1", "mean"))
                         .reset_index()
                         .sort_values(["intent", "pct_sig"], ascending=[True, False]))

    fig, ax = plt.subplots(figsize=(10, 5))
    intent_y = {"high": 2, "moderate": 1, "low": 0}
    for _, row in df_agg.iterrows():
        y = intent_y.get(row["intent"], 0)
        # Jitter x slightly for readability
        ax.scatter(row["pct_sig"] * 100, y + np.random.uniform(-0.15, 0.15),
                   s=row["n"] * 80,
                   color=COLOURS.get(row["intent"], COLOURS["primary"]),
                   alpha=0.75, edgecolors="white", linewidth=0.5)
        ax.annotate(row["category_name"].replace(", beds, and pillows", ""),
                    xy=(row["pct_sig"] * 100, y + np.random.uniform(-0.15, 0.15)),
                    fontsize=8, ha="left", va="center",
                    xytext=(4, 0), textcoords="offset points")

    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(["Low intent", "Moderate intent", "High intent"])
    ax.set_xlabel("% of brands where SoS Granger-causes consideration (p < 0.1)")
    ax.set_xlim(-5, 110)
    ax.axvline(50, color="grey", linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_title("Granger Causality: Does search data predict future brand consideration?\n"
                 "(Bubble size = number of brands tested)", fontweight="bold")
    _save("04_granger_summary")


# ---------------------------------------------------------------------------
# Plot 5: Category-level correlation comparison (forest plot)
# ---------------------------------------------------------------------------

def plot_category_forest(df_brand_r: pd.DataFrame) -> None:
    """
    Forest plot: mean within-brand r (with 95% CI) per category,
    ordered by intent level.
    """
    from scipy.stats import t as t_dist

    cat_summary = []
    for (cat, intent), grp in df_brand_r.groupby(["category_name", "intent"]):
        zs = np.arctanh(grp["r"].clip(-0.999, 0.999))
        mean_r = float(np.tanh(zs.mean()))
        n = len(zs)
        se = 1.0 / np.sqrt(max(n - 3, 1))
        ci_lo = float(np.tanh(zs.mean() - 1.96 * se))
        ci_hi = float(np.tanh(zs.mean() + 1.96 * se))
        cat_summary.append({"category_name": cat, "intent": intent,
                              "mean_r": mean_r, "ci_lo": ci_lo, "ci_hi": ci_hi, "n": n})

    df_sum = pd.DataFrame(cat_summary)
    order_map = {"high": 0, "moderate": 1, "low": 2}
    df_sum["_ord"] = df_sum["intent"].map(order_map)
    df_sum = df_sum.sort_values(["_ord", "mean_r"], ascending=[True, False])

    fig, ax = plt.subplots(figsize=(9, max(5, len(df_sum) * 0.6)))
    for i, (_, row) in enumerate(df_sum.iterrows()):
        colour = COLOURS.get(row["intent"], COLOURS["primary"])
        ax.barh(i, row["mean_r"], color=colour, alpha=0.75, height=0.6)
        ax.errorbar(row["mean_r"], i,
                    xerr=[[row["mean_r"] - row["ci_lo"]],
                           [row["ci_hi"] - row["mean_r"]]],
                    fmt="none", color="black", capsize=3, linewidth=1.2)
        ax.text(row["mean_r"] + 0.01, i,
                f"r={row['mean_r']:.2f}  n={row['n']}",
                va="center", fontsize=8.5)

    ax.set_yticks(range(len(df_sum)))
    ax.set_yticklabels(df_sum["category_name"].str.replace(", beds, and pillows", ""), fontsize=9)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Mean within-brand Pearson r (SoS ↔ Consideration)")
    ax.set_title("How strongly does Share of Search track with Brand Consideration?\n"
                 "(Within-brand, over time)", fontweight="bold")

    legend_patches = [mpatches.Patch(color=COLOURS[i], label=INTENT_LABELS[i])
                      for i in INTENT_ORDER if i in df_sum["intent"].values]
    ax.legend(handles=legend_patches, loc="lower right", fontsize=9)
    _save("05_category_forest_plot")


# ---------------------------------------------------------------------------
# Plot 6: Rank correlation over time (explainability plot for non-technical)
# ---------------------------------------------------------------------------

def plot_rank_stability(df: pd.DataFrame, category: str) -> None:
    """
    For a given category, show whether brand ranks by SoS and by consideration
    are stable over time. This is the "trust" plot — does SoS rank agree with
    the survey rank?
    """
    sub = df[df["category_name"] == category].dropna(
        subset=["share_of_search", "consideration"])
    dates = sorted(sub["date"].unique())
    # Pick 4 evenly spaced dates
    selected_dates = [dates[i] for i in np.linspace(0, len(dates)-1, min(4, len(dates))).astype(int)]

    fig, axes = plt.subplots(1, len(selected_dates), figsize=(4 * len(selected_dates), 5))
    if len(selected_dates) == 1:
        axes = [axes]

    for ax, date in zip(axes, selected_dates):
        snap = sub[sub["date"] == date].copy()
        snap["sos_rank"] = snap["share_of_search"].rank(ascending=False)
        snap["cons_rank"] = snap["consideration"].rank(ascending=False)
        snap = snap.sort_values("cons_rank")

        for _, row in snap.iterrows():
            ax.plot([0, 1], [row["sos_rank"], row["cons_rank"]],
                    color=COLOURS["primary"], alpha=0.5, linewidth=1.5)
            ax.text(-0.05, row["sos_rank"], row["brand_name"][:10],
                    ha="right", fontsize=7.5, va="center")
            ax.text(1.05, row["cons_rank"], row["brand_name"][:10],
                    ha="left", fontsize=7.5, va="center")

        ax.set_xlim(-0.6, 1.6)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Search rank", "Survey rank"])
        ax.set_yticks([])
        ax.invert_yaxis()
        ax.set_title(date.strftime("%b %Y"), fontsize=10)

    fig.suptitle(f"{category}\nDoes search rank agree with survey rank?",
                 fontsize=12, fontweight="bold")
    _save(f"06_rank_stability_{category.replace(' ', '_').replace(',','')[:30]}")
