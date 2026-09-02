"""Core synthetic control method (Abadie-Diamond-Hainmueller style).

Simplified "outcome-only" variant: donor weights are fit to match the
treated unit's pre-treatment *path* directly, with no separate predictor
covariates. This is standard practice for financial/asset-price
applications where a clean set of independent covariates isn't available
(e.g. the classic Brexit-pound synthetic control uses just exchange-rate
history) — see README.md for why this differs from Abadie's original
California-tobacco setup, which used several economic predictor variables.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _project_to_simplex(v: np.ndarray) -> np.ndarray:
    """Euclidean projection of a vector onto the probability simplex {w: w>=0, sum(w)=1}.

    Standard algorithm (Duchi et al. 2008, "Efficient Projections onto the
    L1-Ball", adapted for the simplex case).
    """
    n = len(v)
    u = np.sort(v)[::-1]
    css = np.cumsum(u) - 1
    ind = np.arange(1, n + 1)
    cond = u - css / ind > 0
    rho = ind[cond][-1]
    theta = css[cond][-1] / rho
    return np.maximum(v - theta, 0)


def fit_weights(treated_pre: pd.Series, donors_pre: pd.DataFrame,
                max_iter: int = 5000, tol: float = 1e-10) -> pd.Series:
    """Find donor weights (>=0, sum to 1) minimizing pre-period squared error vs the treated unit.

    Solves the constrained least-squares problem via projected gradient
    descent onto the probability simplex — a standard, dependency-light way
    to solve this convex QP exactly. Two alternatives were tried and
    rejected first: (1) SLSQP (scipy's general-purpose constrained
    optimizer) proved numerically unreliable at this problem's scale,
    silently stalling at the equal-weight initial guess on real sector-price
    data; (2) plain NNLS (enforcing only w>=0, then rescaling to sum to 1)
    let a single highly-correlated donor dominate the fit — sector ETFs are
    strongly collinear with each other, and unconstrained least squares
    concentrates weight on whichever one correlates best rather than
    spreading it, a classic multicollinearity failure mode. Projected
    gradient descent enforces both constraints throughout the optimization,
    not just at the end, which avoids both failure modes.
    """
    donors = donors_pre.columns.tolist()
    X = donors_pre.values  # shape (T, n)
    y = treated_pre.values
    n = X.shape[1]

    XtX = X.T @ X
    Xty = X.T @ y
    lipschitz = np.linalg.eigvalsh(XtX)[-1]
    step = 1.0 / lipschitz if lipschitz > 0 else 1.0

    w = np.full(n, 1.0 / n)
    for _ in range(max_iter):
        grad = 2 * (XtX @ w - Xty)
        w_new = _project_to_simplex(w - step * grad)
        if np.max(np.abs(w_new - w)) < tol:
            w = w_new
            break
        w = w_new
    return pd.Series(w, index=donors)


def synthetic_path(weights: pd.Series, donors_full: pd.DataFrame) -> pd.Series:
    """Apply fitted weights across the FULL time range (pre+post) to build the counterfactual."""
    return donors_full[weights.index] @ weights


def treatment_effect(treated_full: pd.Series, synthetic: pd.Series, treatment_date) -> pd.DataFrame:
    """Gap = actual - synthetic for every period, tagged pre/post the treatment date."""
    gap = treated_full - synthetic
    df = pd.DataFrame({"actual": treated_full, "synthetic": synthetic, "gap": gap})
    df["period"] = np.where(df.index <= pd.Timestamp(treatment_date), "pre", "post")
    return df


def label_segments(df: pd.DataFrame, fit_end, treatment_date) -> pd.DataFrame:
    """Label each row 'fit' (used to fit the synthetic weights), 'confound'
    (after the fit window but still before treatment — an out-of-sample
    check on whether a gap was already emerging BEFORE the event happened),
    or 'post' (after the treatment date).

    When fit_end == treatment_date, 'confound' is empty and this collapses
    to an ordinary pre/post split. Using an earlier fit_end is how you test
    whether a pre-treatment divergence already existed before the event —
    if the 'confound' segment's gap is already large, the 'post' segment's
    gap can't be cleanly attributed to the treatment.
    """
    fit_end_ts = pd.Timestamp(fit_end)
    treatment_ts = pd.Timestamp(treatment_date)
    out = df.copy()
    conditions = [
        out.index <= fit_end_ts,
        (out.index > fit_end_ts) & (out.index <= treatment_ts),
    ]
    out["segment"] = np.select(conditions, ["fit", "confound"], default="post")
    return out


def pre_period_fit_quality(df: pd.DataFrame) -> dict:
    """RMSE of the synthetic fit during the pre-period only — sanity-check before trusting the post-period gap.

    A poor pre-period fit means the donor pool couldn't reconstruct the
    treated unit's history well, so any post-period gap is unreliable —
    always check this before reading the treatment effect.
    """
    pre = df[df["period"] == "pre"]
    rmse = float(np.sqrt(np.mean((pre["actual"] - pre["synthetic"]) ** 2)))
    return {"pre_rmse": round(rmse, 4), "n_pre_periods": len(pre)}


def segment_fit_quality(df: pd.DataFrame, segment: str = "fit") -> dict:
    """Like pre_period_fit_quality, but works off label_segments()'s 'segment'
    column instead of treatment_effect()'s 'period' column — use this when
    fit_end differs from the treatment date (see label_segments)."""
    subset = df[df["segment"] == segment]
    rmse = float(np.sqrt(np.mean((subset["actual"] - subset["synthetic"]) ** 2)))
    return {"rmse": round(rmse, 4), "n_periods": len(subset)}


def placebo_test(treated_col: str, all_units: pd.DataFrame, treatment_date) -> pd.DataFrame:
    """Re-run the fit treating EACH unit as if it were the treated one (donor pool = the rest).

    This is the standard synthetic-control significance check (Abadie et al.)
    in place of a parametric p-value: if the real treated unit's post-period
    gap isn't clearly larger than the gaps produced by re-running the same
    method on units that were NOT specifically exposed to the event via the
    hypothesized channel, that's a sign the "effect" may just be estimation
    noise rather than a real pivot-driven divergence.
    """
    pre_mask = all_units.index <= pd.Timestamp(treatment_date)
    results = []
    for unit in all_units.columns:
        donors = all_units.drop(columns=[unit])
        w = fit_weights(all_units.loc[pre_mask, unit], donors.loc[pre_mask])
        synth = synthetic_path(w, donors)
        df = treatment_effect(all_units[unit], synth, treatment_date)
        post_gap = df.loc[df["period"] == "post", "gap"]
        results.append({
            "unit": unit,
            "is_treated": unit == treated_col,
            "mean_post_gap_pct": round(float(post_gap.mean()), 3),
            "max_abs_post_gap_pct": round(float(post_gap.abs().max()), 3),
        })
    return pd.DataFrame(results).sort_values(
        "mean_post_gap_pct", key=lambda s: s.abs(), ascending=False
    ).reset_index(drop=True)
