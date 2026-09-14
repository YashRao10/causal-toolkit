# Causal Toolkit — generalized synthetic-control case studies

A standalone research instrument: point it
at *any* macro/company event and *any* treated ticker, and it runs a rigorous synthetic-control
test (Abadie-Diamond-Hainmueller, outcome-only variant) to check whether the event actually
caused a measurable break from a hand-picked peer/donor group, or whether the "effect" is just
riding a pre-existing trend / estimation noise.

Grew out of an earlier one-off Fed-pivot-vs-Tech-sector test; that script's core
method (`synthetic_control.py`) is fully generic and carried here unchanged, and this toolkit
generalizes the *data* and *interface* layers so the method can be pointed at new questions
without writing a new one-off script each time.

## Quickstart

```bash
pip install -r requirements.txt
python run.py fed_pivot_tech          # one case study
python run.py all                     # every case study in case_studies.py
```

Opens `reports/<case_study_key>.html` — a self-contained report (no CDN, no JS libraries):
an actual-vs-synthetic chart with a hover crosshair, fit-quality numbers, the placebo-test
table, and a written verdict. Every run also regenerates `reports/index.html` — a browsable
list of every case study run so far, newest first, each with a status badge (real effect /
not a clear effect / loose fit / fit too poor to trust) pulled from that report's own verdict.
Plain files, auto-regenerated, no server.

## Adding a new case study

Add an entry to `CASE_STUDIES` in `case_studies.py`:

```python
"my_case": {
    "title": "...",
    "description": "...",
    "treated": "TICKER",
    "donors": ["PEER1", "PEER2"],   # hand-picked — see "On donor pools" below
    "treatment_date": "YYYY-MM-DD",
    "fit_end": "YYYY-MM-DD",        # == treatment_date for a plain pre/post split;
                                     # earlier for a confound-window check (see below)
    "pre_start": "YYYY-MM-DD",
},
```

Then `python run.py my_case`.

## On donor pools — the one thing this tool won't do for you

The donor/peer pool is **always hand-picked by the analyst**, never algorithmically matched.
For sector-vs-sector tests the obvious donor pool is "the other sectors" (already built into
`SECTOR_ETFS`). For an individual stock, there usually isn't an equally obvious peer group —
picking one is a real judgment call about what the treated unit's counterfactual *should* look
like, and baking that judgment into the tool would hide it rather than surface it. State your
peer group, then let the fit-quality check tell you if it was a reasonable choice.

## The fit-quality gate — read this before trusting any gap

`run.py` computes the fit-window RMSE relative to the treated unit's own fit-window standard
deviation. If that ratio is:

- **> 1.0** — the donor pool cannot reconstruct the treated unit's own pre-period path at all.
  The report's verdict section leads with a hard "do not trust the gap" warning and stops there
  — this almost always means the donor pool is wrong for this unit, not that a real effect was
  found. (Found this the hard way building the `be_short_seller` case study — see below.)
- **0.5–1.0** — a loose fit; the verdict is labeled "suggestive at best."
- **< 0.5** — a reasonable fit; the gap is worth reading.

This mirrors `synthetic_control.py`'s own `pre_period_fit_quality()` docstring ("always check
this before reading the treatment effect") — the gate just makes sure a verdict can't be written
without actually checking it.

## Case studies included

1. **`fed_pivot_tech`** — validation case, reproduces the original one-off script's
   finding (XLK's gap vs. the other 10 sectors opened up *before* the June 2026 FOMC
   pivot, so the pivot can't cleanly take credit for it). Confirms the generalized toolkit
   recovers the same honest, negative result as that script.
2. **`be_short_seller`** — did Bloom Energy's Hunterbrook short-seller report (2026-07-08) break
   it from its clean-energy peers (FCEL, PLUG)? **Real methodological lesson while building
   this:** the first attempt used a 2-year pre-period (matching the Fed-pivot case) and failed
   the fit-quality gate outright (relative RMSE 1.28×) — BE's own multi-year rally is so much
   larger than FCEL/PLUG's that no combination of them can reconstruct it over that window. Cut
   the pre-period to ~4 months (standard fix when the treated unit has a strong idiosyncratic
   long-run trend) and got a real, honest result: BE's post-report gap actually ranks **last** of
   the 3 units in the placebo test — its decline doesn't stand out as unusually large versus its
   own peer group's noise in that window. Not the "yes, real breakage" story a reader might
   expect going in.
3. **`tsla_earnings_miss_auto_peers`** — did TSLA's genuine Jul 22 earnings miss break it from
   real auto/EV peers (F, GM, RIVN)? Fails the fit-quality gate outright (relative RMSE 1.78×) —
   the chart shows TSLA running *below* its synthetic counterfactual for almost the entire
   pre-period, not just after earnings, meaning it simply doesn't move with these peers
   day-to-day at all.
4. **`tsla_earnings_miss_growth_peers`** — same event, re-tested against RIVN/LCID/PLTR/COIN
   (EV + retail-favorite high-beta growth names) instead of Detroit automakers. Improves the fit
   (relative RMSE 1.29×, down from 1.78×) but still fails the gate. Read together, these two are
   the toolkit's clearest demonstration of an honest "the method can't cleanly isolate an effect
   here" result: TSLA is genuinely idiosyncratic enough that no simple hand-picked donor pool
   tried so far reconstructs it, which is itself informative rather than a tooling failure.
5. **`googl_capex_guidance`** — did GOOGL's Jul 22 capex-guidance selloff ($190B guidance
   crushing FCF margin despite 63% YoY cloud growth) break it from fellow Mag-7 hyperscalers
   (MSFT, META, AMZN)? **Good fit this time** (relative RMSE 0.46×) — and the placebo test finds
   GOOGL's own post-period gap (-3.47%) is actually the *smallest* of the 4 units (MSFT's
   placebo gap was -9.22%, larger). Read: this looks like a shared "market re-pricing hyperscaler
   AI-capex risk" move across the whole group that week, not a GOOGL-specific punishment for its
   own guidance — a genuinely non-obvious result.
6. **`fomc_pivot_utilities`** — reuses the exact validated Fed-pivot event/date, swapping the
   treated unit to XLU, to test the "classic rate-sensitive bond-proxy sector" theory directly
   (substituted for a literal single-day "AI-datacenter-power" test, since that theme doesn't
   have one clean, independently verifiable catalyst date). Result: XLU ranks **last** (#11 of
   11) in the placebo test — no distinctive Fed-pivot effect on Utilities shows up in this test,
   contradicting the textbook prior.
7. **`sndk_supply_glut_fear`** — did SanDisk's Jul 2, 2026 supply-glut selloff (~14% intraday,
   ~11% close to close) break it from its memory-chip peers (WDC, MU, STX, NTAP)? 7/2 was one of
   several repeated "supply glut fear" selloffs that hit the group through Jul-Sep 2026 (further
   echoes on 7/13, 7/29, 8/6, 8/18, 9/10) — chosen here as the largest single-day move rather than
   modeling the whole multi-month sequence at once. **Fails the fit-quality gate** (relative RMSE
   1.02×) — the donor pool cannot reconstruct SNDK's own 6-month pre-period path, so the post-
   period gap isn't trustworthy either way. Shipped as an honest negative result, same as the TSLA
   cases: no better-fitting donor pool was substituted in to force a cleaner-looking answer.
8. **`msft_earnings_record_pop`** — mirror case of `googl_capex_guidance`: did MSFT's Jul 30, 2026
   earnings report (Azure guidance beat, stock +16%, ~$450B added — the largest single-day
   market-cap gain on record for any company) outpace fellow hyperscalers (GOOGL, META, AMZN), or
   did the whole group re-rate on the same signal? **Loose fit** (relative RMSE 0.83×) — treat as
   suggestive, not clean. MSFT's post-period gap ranks #2 of 4 in the placebo test, which does
   **not** read as a clearly unit-specific effect: other units in the donor pool show gaps of
   similar or larger size, consistent with the whole hyperscaler group moving together on
   improving AI-monetization evidence that week rather than MSFT alone getting rewarded.

9. **`mu_meta_compute_chip_glut_fear`** — did Micron's Jul 1, 2026 selloff (-10.6%) break it from
   fellow AI-chip suppliers (AMD, NVDA, INTC), or hit the whole group? Meta announced "Meta
   Compute" that day, a plan to resell its own excess AI infrastructure, which the market read
   as a sign hyperscaler GPU demand might be peaking rather than perpetually scarce; chip
   suppliers sold off hard (Philadelphia Semiconductor Index down over 10% across two sessions)
   even as META itself rose ~9% on its own news. Different mechanism from
   `sndk_supply_glut_fear` (that one was NAND/DRAM oversupply; this one is AI-chip demand-
   destruction fear). **Good fit** (relative RMSE 0.35x) — MU ranks #2 of 4 in the placebo test,
   reading as NOT a company-specific effect: the whole chip-supplier group re-priced together on
   the same news, a clean confirmatory result unlike the SNDK case's inconclusive one.

_A planned 10th case (`ntap_ai_quarter_beat` — NetApp's Sep 11, 2026 AI-driven earnings beat
against the same storage/memory peer group as case 7, testing whether a genuine positive surprise
fares differently from SNDK's fear-driven selloff) was **shelved before shipping**: the event is
only a few days old as of this writing and yfinance has zero trading days of post-treatment data
yet (post-period gap computed as NaN). Revisit once at least a few trading days have passed._

## Tests

```bash
pip install -r requirements-dev.txt
pytest test_synthetic_control.py
```

Pure toy-data unit tests on the core method, no network calls.
