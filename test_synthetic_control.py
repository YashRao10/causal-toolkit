"""Unit tests for synthetic_control.py — synthetic/toy data only, no network.

Pure numeric tests against
a known-answer synthetic dataset, not sensitive to any real market data.
"""
import numpy as np
import pandas as pd
import pytest

from synthetic_control import fit_weights, synthetic_path, treatment_effect, pre_period_fit_quality


def _make_toy_data(n_days=100, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    donor_a = pd.Series(100 + np.cumsum(rng.normal(0, 1, n_days)), index=dates)
    donor_b = pd.Series(100 + np.cumsum(rng.normal(0, 1, n_days)), index=dates)
    donor_c = pd.Series(100 + np.cumsum(rng.normal(0, 1, n_days)), index=dates)
    donors = pd.DataFrame({"A": donor_a, "B": donor_b, "C": donor_c})
    # Treated unit is a KNOWN combination of donors (60% A, 40% B, 0% C) + tiny noise
    true_weights = {"A": 0.6, "B": 0.4, "C": 0.0}
    treated = 0.6 * donor_a + 0.4 * donor_b + rng.normal(0, 0.05, n_days)
    return treated, donors, true_weights


def test_fit_weights_recovers_known_combination():
    treated, donors, true_weights = _make_toy_data()
    weights = fit_weights(treated, donors)
    assert weights.sum() == pytest.approx(1.0, abs=1e-6)
    assert (weights >= -1e-9).all()
    assert weights["A"] == pytest.approx(true_weights["A"], abs=0.05)
    assert weights["B"] == pytest.approx(true_weights["B"], abs=0.05)
    assert weights["C"] == pytest.approx(true_weights["C"], abs=0.05)


def test_synthetic_path_matches_treated_absent_shock():
    treated, donors, _ = _make_toy_data()
    weights = fit_weights(treated, donors)
    synth = synthetic_path(weights, donors)
    rmse = np.sqrt(np.mean((treated - synth) ** 2))
    assert rmse < 0.5  # tight fit expected since treated IS a combination of donors + tiny noise


def test_treatment_effect_detects_injected_shock():
    treated, donors, _ = _make_toy_data(n_days=150)
    treatment_date = treated.index[99]
    # Inject an artificial +5 point shock after the treatment date
    treated_shocked = treated.copy()
    treated_shocked.loc[treated_shocked.index > treatment_date] += 5.0

    pre_mask = treated_shocked.index <= treatment_date
    weights = fit_weights(treated_shocked[pre_mask], donors[pre_mask])
    synth = synthetic_path(weights, donors)
    effect_df = treatment_effect(treated_shocked, synth, treatment_date)

    pre_gap_mean = effect_df.loc[effect_df["period"] == "pre", "gap"].mean()
    post_gap_mean = effect_df.loc[effect_df["period"] == "post", "gap"].mean()
    assert abs(pre_gap_mean) < 0.5     # near-zero gap before the shock
    assert post_gap_mean > 4.0         # shock recovered post-period


def test_pre_period_fit_quality_reports_low_rmse_for_good_fit():
    treated, donors, _ = _make_toy_data()
    weights = fit_weights(treated, donors)
    synth = synthetic_path(weights, donors)
    effect_df = treatment_effect(treated, synth, treated.index[-1])  # everything "pre" here
    quality = pre_period_fit_quality(effect_df)
    assert quality["pre_rmse"] < 0.5
    assert quality["n_pre_periods"] == len(treated)
