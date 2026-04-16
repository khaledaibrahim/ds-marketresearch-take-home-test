"""
analysis.py
-----------
All statistical functions for the Share of Search ↔ Brand Health study.

Analysis layers:
  1. Cross-sectional correlation: SoS vs consideration across brands at each date
  2. Within-brand longitudinal correlation: changes in SoS vs changes in consideration
  3. Cross-lagged correlation: does SoS at t predict consideration at t+k?
  4. Granger causality: formal test of whether SoS Granger-causes consideration
  5. Category comparison: do high-intent categories show stronger relationships?

Statistical choices:
  - Pearson r for contemporaneous correlations (data is continuous, roughly normal)
  - First-differencing before Granger tests to reduce autocorrelation bias
  - ADF test to check stationarity; first-difference if non-stationary
  - Fisher's z for averaging and comparing correlation coefficients
  - Bootstrap CIs for robustness where sample sizes are small
"""

import warnings
import numpy as np
import pandas as pd
import scipy.stats as stats
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

warnings.filterwarnings("ignore")


# ---------------------------------------------------------------------------
# 1. Cross-sectional (brand-level) correlation
# ---------------------------------------------------------------------------

def cross_sectional_correlation(df: pd.DataFrame,
                                outcome: str = "consideration") -> pd.DataFrame:
    """
    For each (category, date), compute Pearson r between SoS and `outcome`
    across the brands available that month.
    Returns a DataFrame with per-date correlations and a category-level summary.
    """
    records = []
    for (cat, date), group in df.groupby(["category_name", "date"]):
        if len(group) < 4:
            continue
        clean = group[["share_of_search", outcome]].dropna()
        if len(clean) < 4:
            continue
        r, p = stats.pearsonr(clean["share_of_search"], clean[outcome])
        records.append({"category_name": cat, "date": date, "r": r, "p": p,
                         "n_brands": len(clean)})

    df_out = pd.DataFrame(records)
    # Category-level summary (Fisher-z mean)
    if df_out.empty:
        summary = pd.DataFrame(columns=["category_name", "mean_r", "ci_lo", "ci_hi", "n_obs"])
        return df_out, summary
    summary = (df_out.groupby("category_name")
                      .apply(_fisher_mean_r, include_groups=False)
                      .reset_index())
    return df_out, summary


def _fisher_mean_r(group: pd.DataFrame) -> pd.Series:
    """Average Pearson r values using Fisher's z transformation."""
    zs = np.arctanh(group["r"].clip(-0.999, 0.999))
    mean_r = float(np.tanh(zs.mean()))
    se = 1.0 / np.sqrt(max(len(zs) - 3, 1))
    ci_lo = float(np.tanh(zs.mean() - 1.96 * se))
    ci_hi = float(np.tanh(zs.mean() + 1.96 * se))
    return pd.Series({"mean_r": mean_r, "ci_lo": ci_lo, "ci_hi": ci_hi, "n_obs": len(group)})


# ---------------------------------------------------------------------------
# 2. Within-brand longitudinal correlation (levels and first differences)
# ---------------------------------------------------------------------------

def within_brand_correlation(df: pd.DataFrame,
                             outcome: str = "consideration",
                             use_diff: bool = False) -> pd.DataFrame:
    """
    For each brand, compute Pearson r between SoS and `outcome` over time.
    If `use_diff=True`, correlate first differences (removes trend bias).
    Returns per-brand results and a category/intent-level summary.
    """
    records = []
    for (cat, brand), grp in df.groupby(["category_name", "brand_name"]):
        grp = grp.sort_values("date")
        x = grp["share_of_search"].dropna()
        y = grp[outcome].dropna()
        idx = x.index.intersection(y.index)
        x, y = x.loc[idx], y.loc[idx]
        if len(x) < 8:
            continue
        if use_diff:
            x, y = x.diff().dropna(), y.diff().dropna()
            idx = x.index.intersection(y.index)
            x, y = x.loc[idx], y.loc[idx]
            if len(x) < 6:
                continue
        r, p = stats.pearsonr(x, y)
        records.append({
            "category_name": cat, "brand_name": brand,
            "intent": grp["intent"].iloc[0],
            "r": r, "p": p, "n_months": len(x),
            "method": "first_diff" if use_diff else "levels",
        })
    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 3. Cross-lagged correlation (leading indicator test)
# ---------------------------------------------------------------------------

def cross_lagged_correlations(df: pd.DataFrame,
                              max_lag: int = 4,
                              outcome: str = "consideration") -> pd.DataFrame:
    """
    For each lag k in 0..max_lag, correlate SoS at time t-k with `outcome` at t.
    A positive correlation peaking at k>0 supports search as a leading indicator.

    Returns a DataFrame: category, lag, mean_r, ci_lo, ci_hi.
    """
    lag_cols = {0: "share_of_search"}
    for k in range(1, max_lag + 1):
        lag_cols[k] = f"sos_lag_{k}"

    records = []
    for lag, col in lag_cols.items():
        if col not in df.columns:
            continue
        brand_rs = []
        for (cat, brand), grp in df.groupby(["category_name", "brand_name"]):
            grp = grp.sort_values("date")
            clean = grp[[col, outcome]].dropna()
            if len(clean) < 8:
                continue
            r, _ = stats.pearsonr(clean[col], clean[outcome])
            brand_rs.append({"category_name": cat, "intent": grp["intent"].iloc[0],
                              "r": r, "lag": lag})

        df_lag = pd.DataFrame(brand_rs)
        if df_lag.empty:
            continue
        for cat, grp_cat in df_lag.groupby("category_name"):
            stats_r = _fisher_mean_r(grp_cat)
            records.append({
                "category_name": cat,
                "intent": grp_cat["intent"].iloc[0],
                "lag": lag, **stats_r
            })

    return pd.DataFrame(records).sort_values(["category_name", "lag"])


# ---------------------------------------------------------------------------
# 4. Granger causality
# ---------------------------------------------------------------------------

def run_granger_tests(df: pd.DataFrame,
                      outcome: str = "consideration",
                      max_lag: int = 3,
                      min_obs: int = 20) -> pd.DataFrame:
    """
    For each brand with sufficient data, test whether Share of Search
    Granger-causes `outcome`.

    H0: SoS does NOT Granger-cause consideration (past SoS adds no predictive
        power beyond past consideration alone).

    We first-difference both series to address non-stationarity, which is
    common in brand-health time series.

    Returns per-brand p-values and a category-level summary.
    """
    def _is_stationary(series: pd.Series, alpha: float = 0.05) -> bool:
        """Return True if ADF test rejects non-stationarity at `alpha`."""
        try:
            _, p, *_ = adfuller(series.dropna(), autolag="AIC")
            return p < alpha
        except Exception:
            return False

    records = []
    for (cat, brand), grp in df.groupby(["category_name", "brand_name"]):
        grp = grp.sort_values("date")
        x = grp["share_of_search"].dropna()
        y = grp[outcome].dropna()
        idx = x.index.intersection(y.index)
        x, y = x.loc[idx], y.loc[idx]

        if len(x) < min_obs:
            continue

        # First-difference if non-stationary
        if not _is_stationary(x) or not _is_stationary(y):
            x, y = x.diff().dropna(), y.diff().dropna()
            idx = x.index.intersection(y.index)
            x, y = x.loc[idx], y.loc[idx]
            differenced = True
        else:
            differenced = False

        if len(x) < min_obs - 2:
            continue

        # Granger test (statsmodels expects [outcome, predictor] order)
        data = pd.DataFrame({"y": y, "x": x}).dropna()
        if len(data) < min_obs:
            continue

        try:
            results = grangercausalitytests(data[["y", "x"]], maxlag=max_lag,
                                            verbose=False)
            # Report the lag with lowest p-value (F-test)
            best_lag = min(results, key=lambda k: results[k][0]["ssr_ftest"][1])
            f_stat, p_val, *_ = results[best_lag][0]["ssr_ftest"]
            records.append({
                "category_name": cat, "brand_name": brand,
                "intent": grp["intent"].iloc[0],
                "best_lag": best_lag, "f_stat": f_stat, "p_value": p_val,
                "differenced": differenced, "n_obs": len(data),
                "significant_0.1": p_val < 0.1,
                "significant_0.05": p_val < 0.05,
            })
        except Exception:
            continue

    return pd.DataFrame(records)


def granger_summary(df_granger: pd.DataFrame) -> pd.DataFrame:
    """Summarise Granger test results by category and intent level."""
    return (df_granger.groupby(["category_name", "intent"])
                      .agg(
                          n_brands=("brand_name", "count"),
                          pct_sig_10=("significant_0.1", "mean"),
                          pct_sig_05=("significant_0.05", "mean"),
                          median_p=("p_value", "median"),
                      )
                      .reset_index()
                      .sort_values("median_p"))


# ---------------------------------------------------------------------------
# 5. Category-level comparison by intent
# ---------------------------------------------------------------------------

def intent_level_comparison(df_brand_r: pd.DataFrame) -> pd.DataFrame:
    """
    Compare mean within-brand correlations across intent levels.
    Returns a summary with Fisher-z mean r per intent level,
    and a Mann-Whitney U test comparing high vs low intent.
    """
    summary = (df_brand_r.groupby("intent")
                          .apply(_fisher_mean_r, include_groups=False)
                          .reset_index())

    # Mann-Whitney U between high and low intent
    high = df_brand_r[df_brand_r["intent"] == "high"]["r"].values
    low  = df_brand_r[df_brand_r["intent"] == "low"]["r"].values
    if len(high) >= 3 and len(low) >= 3:
        u_stat, p_mw = stats.mannwhitneyu(high, low, alternative="greater")
        summary.attrs["mannwhitney_p"] = p_mw
        summary.attrs["mannwhitney_u"] = u_stat

    return summary


# ---------------------------------------------------------------------------
# Utility: compute brand-level Share of Search rank and survey rank
# ---------------------------------------------------------------------------

def compute_rank_correlation(df: pd.DataFrame,
                             outcome: str = "consideration") -> pd.DataFrame:
    """
    For each (category, date), compute Spearman rank correlation between
    SoS rank and `outcome` rank across brands.
    Rank correlations are more robust and easier to explain to non-technical
    audiences ("brands that rank higher on search also tend to rank higher on
    consideration").
    """
    records = []
    for (cat, date), grp in df.groupby(["category_name", "date"]):
        clean = grp[["share_of_search", outcome]].dropna()
        if len(clean) < 4:
            continue
        r_sp, p_sp = stats.spearmanr(clean["share_of_search"], clean[outcome])
        records.append({"category_name": cat, "date": date,
                         "spearman_r": r_sp, "p": p_sp, "n": len(clean)})
    return pd.DataFrame(records)
