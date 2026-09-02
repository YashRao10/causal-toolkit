"""Entrypoint: run a named case study end to end and write an HTML report.

Usage:
    cd causal-toolkit
    pip install -r requirements.txt
    python run.py fed_pivot_tech
    python run.py be_short_seller
    python run.py fomc_pivot_utilities
    python run.py all          # runs every case study in case_studies.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import pandas as pd

from case_studies import CASE_STUDIES
from data import fetch_daily_levels
from synthetic_control import (
    fit_weights, synthetic_path, treatment_effect, pre_period_fit_quality,
    label_segments, segment_fit_quality, placebo_test,
)
import report
import index as index_page


def _write_verdict(
    config: dict, effect_df: pd.DataFrame, placebo_df: pd.DataFrame, relative_rmse: float
) -> str:
    treated = config["treated"]
    treated_row = placebo_df[placebo_df["unit"] == treated].iloc[0]
    rank = (placebo_df["mean_post_gap_pct"].abs() >= abs(treated_row["mean_post_gap_pct"])).sum()
    n_units = len(placebo_df)

    has_confound_window = config["fit_end"] != config["treatment_date"]
    confound_gap = None
    if has_confound_window and "segment" in effect_df.columns:
        confound_rows = effect_df[effect_df["segment"] == "confound"]
        if len(confound_rows):
            confound_gap = confound_rows["gap"].mean()

    post_gap = effect_df.loc[
        effect_df.get("segment", effect_df["period"]).isin(["post"]), "gap"
    ].mean()

    parts = []

    # Fit-quality gate comes FIRST and can override everything below — a gap
    # computed from a synthetic path that never resembled the treated unit's
    # own history isn't a gap worth reading at all (see synthetic_control.py's
    # own pre_period_fit_quality docstring: "always check this before reading
    # the treatment effect").
    if relative_rmse > 1.0:
        parts.append(
            f"<p><strong>Do not trust the gap below.</strong> The fit-window RMSE is "
            f"<strong>{relative_rmse:.2f}&times;</strong> this unit's own fit-window standard "
            f"deviation — the donor pool literally cannot reconstruct {treated}'s pre-period "
            f"path at all, which usually means the donor pool is the wrong choice for this "
            f"unit (e.g. {treated} moved for reasons entirely disconnected from the donors' own "
            f"drivers), not that a real effect was found. Pick a different/better-correlated "
            f"donor pool before drawing any conclusion from this run.</p>"
        )
        return "\n".join(parts)
    elif relative_rmse > 0.5:
        parts.append(
            f"<p><strong>Caution on fit quality:</strong> the fit-window RMSE is "
            f"{relative_rmse:.2f}&times; this unit's own fit-window standard deviation — a loose "
            f"fit. Treat the gap below as suggestive at best, not a clean read.</p>"
        )

    parts.append(
        f"<p><strong>{treated}</strong>'s post-period gap ranks <strong>#{rank} of {n_units}</strong> "
        f"units by absolute size in the placebo test (larger rank = more likely a real, "
        f"unit-specific effect rather than noise the method would produce for any random unit)."
        f"</p>"
    )
    if confound_gap is not None:
        if abs(confound_gap) > abs(post_gap) * 0.25:
            parts.append(
                f"<p><strong>Caution:</strong> the confound-window gap ({confound_gap:+.2f}) is "
                f"already a substantial fraction of the post-period gap ({post_gap:+.2f}) — this "
                f"divergence looks like it was emerging <em>before</em> the treatment date, so the "
                f"treatment can't cleanly take full credit for the post-period gap.</p>"
            )
        else:
            parts.append(
                f"<p>The confound-window gap ({confound_gap:+.2f}) is small relative to the "
                f"post-period gap ({post_gap:+.2f}) — the divergence looks genuinely tied to the "
                f"treatment date, not a pre-existing trend.</p>"
            )
    if rank <= max(1, n_units // 3):
        parts.append(
            "<p><strong>Read:</strong> this looks like a real, unit-specific effect — the gap this "
            "method finds for the treated unit is larger than what it produces when re-run on most "
            "other units in the donor pool.</p>"
        )
    else:
        parts.append(
            "<p><strong>Read:</strong> this does NOT look like a clearly unit-specific effect — "
            "other units in the placebo test show gaps of similar or larger size, so this could "
            "just be estimation noise rather than a real, distinct move.</p>"
        )
    return "\n".join(parts)


def _verdict_headline(relative_rmse: float, rank: int, n_units: int) -> tuple[str, str]:
    """Short (badge_class, label) pair summarizing the verdict for the index page."""
    if relative_rmse > 1.0:
        return "bad-fit", "Fit too poor to trust"
    if relative_rmse > 0.5:
        return "loose-fit", "Loose fit — suggestive at best"
    if rank <= max(1, n_units // 3):
        return "real-effect", "Real, unit-specific effect"
    return "no-effect", "Not a clear unit-specific effect"


def run_one(key: str) -> str:
    config = CASE_STUDIES[key]
    all_tickers = [config["treated"]] + config["donors"]
    print(f"[{key}] fetching {', '.join(all_tickers)} from {config['pre_start']}...")
    levels = fetch_daily_levels(all_tickers, config["pre_start"])

    fit_mask = levels.index <= pd.Timestamp(config["fit_end"])
    weights = fit_weights(levels.loc[fit_mask, config["treated"]], levels.loc[fit_mask, config["donors"]])
    synth = synthetic_path(weights, levels[config["donors"]])
    effect_df = treatment_effect(levels[config["treated"]], synth, config["treatment_date"])
    effect_df = label_segments(effect_df, config["fit_end"], config["treatment_date"])

    if config["fit_end"] == config["treatment_date"]:
        fit_quality = pre_period_fit_quality(effect_df)
    else:
        fit_quality = segment_fit_quality(effect_df, "fit")

    rmse = fit_quality.get("rmse", fit_quality.get("pre_rmse"))
    treated_fit_std = levels.loc[fit_mask, config["treated"]].std()
    relative_rmse = rmse / treated_fit_std if treated_fit_std else float("inf")

    placebo_df = placebo_test(config["treated"], levels, config["treatment_date"])
    verdict = _write_verdict(config, effect_df, placebo_df, relative_rmse)

    treated_row = placebo_df[placebo_df["unit"] == config["treated"]].iloc[0]
    rank = (placebo_df["mean_post_gap_pct"].abs() >= abs(treated_row["mean_post_gap_pct"])).sum()
    badge_class, badge_label = _verdict_headline(relative_rmse, rank, len(placebo_df))

    generated_at_dt = datetime.now(timezone.utc)
    generated_at = generated_at_dt.strftime("%Y-%m-%d %H:%M UTC")
    html = report.render(
        key, config, effect_df, fit_quality, placebo_df, verdict, generated_at, relative_rmse
    )

    os.makedirs("reports", exist_ok=True)
    out_path = f"reports/{key}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    meta = {
        "key": key,
        "title": config["title"],
        "description": config["description"],
        "treated": config["treated"],
        "generated_at": generated_at,
        "generated_at_iso": generated_at_dt.isoformat(),
        "badge_class": badge_class,
        "badge_label": badge_label,
    }
    with open(f"reports/{key}.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[{key}] wrote {out_path}")
    index_page.rebuild()
    return out_path


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: python run.py <case_study_key>|all")
    key = sys.argv[1]
    if key == "all":
        for k in CASE_STUDIES:
            run_one(k)
    elif key in CASE_STUDIES:
        run_one(key)
    else:
        sys.exit(f"Unknown case study '{key}'. Options: {', '.join(CASE_STUDIES)}, all")


if __name__ == "__main__":
    main()
