"""Case-study configs. Each one names a treated ticker, a donor pool, and a
treatment date — the donor pool is always picked by hand (a peer group the
analyst believes is a reasonable counterfactual), never algorithmically
guessed. See README for why.
"""
from __future__ import annotations

SECTOR_ETFS = ["XLK", "XLE", "XLU", "XLF", "XLV", "XLY", "XLP", "XLI", "XLB", "XLRE", "XLC"]

CASE_STUDIES = {
    "fed_pivot_tech": {
        "title": "Did the June 2026 Fed hawkish pivot actually move Tech?",
        "description": (
            "Validation case — reproduces the original one-off script's "
            "finding. Confirms the generalized toolkit "
            "recovers the same (honest, negative) result: XLK's gap vs. its "
            "synthetic counterfactual opened up months before the June 17 FOMC "
            "meeting, so the pivot itself can't cleanly take credit for it."
        ),
        "treated": "XLK",
        "donors": [t for t in SECTOR_ETFS if t != "XLK"],
        "treatment_date": "2026-06-17",
        "fit_end": "2026-02-15",  # matches the original confound-check run
        "pre_start": "2024-06-17",
    },
    "be_short_seller": {
        "title": "Did Bloom Energy's Hunterbrook short-seller report break it from clean-energy peers?",
        "description": (
            "Treated: BE. Donors: FCEL, PLUG (fuel-cell/clean-hydrogen peers) — "
            "a hand-picked peer group, not an algorithmic match. Treatment date "
            "is the Hunterbrook Capital report (2026-07-08). Tests whether BE's "
            "decline is company-specific (a real post-treatment gap vs. peers) "
            "or just riding the same clean-energy/rate-sensitive-growth wave "
            "FCEL and PLUG were already on. Pre-period deliberately short "
            "(~4 months, not 2 years): BE's own multi-year rally is so much "
            "larger than FCEL/PLUG's that a long window makes the donor pool "
            "unusable (see README) — a short window centered on BE's recent "
            "behavior is the standard fix when the treated unit has a strong "
            "idiosyncratic long-run trend."
        ),
        "treated": "BE",
        "donors": ["FCEL", "PLUG"],
        "treatment_date": "2026-07-08",
        "fit_end": "2026-07-08",
        "pre_start": "2026-03-01",
    },
    "tsla_earnings_miss_auto_peers": {
        "title": "Did TSLA's Jul 22 earnings miss actually break it from auto/EV peers?",
        "description": (
            "Treated: TSLA. Donors: F, GM, RIVN (traditional + EV auto peers) — "
            "hand-picked, not algorithmic. Treatment date is the Jul 22 earnings "
            "report (auto gross margins 16.3% vs 18.4% expected, EPS $0.33 vs "
            "$0.55 consensus, FCF went negative on AI/robotics capex). Tests "
            "whether the post-earnings selloff is a real, company-specific "
            "fundamentals break from the auto sector, or whether TSLA was "
            "already diverging from these peers beforehand for unrelated "
            "reasons. Result: fails the fit-quality gate — see "
            "tsla_earnings_miss_growth_peers for the follow-up with a "
            "different donor pool."
        ),
        "treated": "TSLA",
        "donors": ["F", "GM", "RIVN"],
        "treatment_date": "2026-07-22",
        "fit_end": "2026-07-22",
        "pre_start": "2026-01-22",
    },
    "tsla_earnings_miss_growth_peers": {
        "title": "TSLA's Jul 22 earnings miss, re-tested against high-beta growth peers instead of automakers",
        "description": (
            "Follow-up to tsla_earnings_miss_auto_peers, which failed the "
            "fit-quality gate — pure Detroit automakers (F, GM) don't move "
            "with TSLA day-to-day at all. Treated: TSLA. Donors: RIVN, LCID "
            "(EV-specific, still auto but more growth-multiple-priced than "
            "F/GM), PLTR, COIN (retail-favorite high-beta momentum names with "
            "no automotive exposure, included on the theory that TSLA trades "
            "more on 'high-beta retail-momentum growth' factor exposure than "
            "on 'automaker' exposure most days). Same Jul 22 earnings-miss "
            "treatment date. Result: improved (relative RMSE 1.29x, down from "
            "1.78x with pure automakers) but still fails the fit-quality gate "
            "— TSLA doesn't reconstruct cleanly from either peer group tried "
            "so far. Read as: TSLA is genuinely idiosyncratic (Musk/narrative "
            "-driven) rather than a donor-pool-selection failure specifically "
            "— a case where the honest answer is 'this method can't cleanly "
            "isolate an effect here,' not a forced conclusion either way."
        ),
        "treated": "TSLA",
        "donors": ["RIVN", "LCID", "PLTR", "COIN"],
        "treatment_date": "2026-07-22",
        "fit_end": "2026-07-22",
        "pre_start": "2026-01-22",
    },
    "googl_capex_guidance": {
        "title": "Did GOOGL's Jul 22 capex-guidance selloff break it from fellow hyperscalers?",
        "description": (
            "Treated: GOOGL. Donors: MSFT, META, AMZN (fellow Mag-7 "
            "hyperscalers, all running their own large AI-capex programs and "
            "facing similar market scrutiny over it) — hand-picked, not "
            "algorithmic. Treatment date is GOOGL's Jul 22 after-close report: "
            "Cloud grew 63% YoY, a strong number, but $190B capex guidance "
            "crushed the FCF margin (21%→10, from 21%→9.2% per prior "
            "notes) and the stock sold off anyway. Tests whether this was a "
            "GOOGL-specific reaction to its own guidance, or part of a "
            "shared 'market re-pricing hyperscaler AI-capex risk' move that "
            "should also show up in the donor pool."
        ),
        "treated": "GOOGL",
        "donors": ["MSFT", "META", "AMZN"],
        "treatment_date": "2026-07-22",
        "fit_end": "2026-07-22",
        "pre_start": "2026-01-22",
    },
    "fomc_pivot_utilities": {
        "title": "Did the same June 2026 FOMC pivot move Utilities the way classic rate-sensitivity theory predicts?",
        "description": (
            "Reuses the exact same validated event/date as fed_pivot_tech, "
            "swapping the treated unit to XLU. Utilities are the textbook "
            "bond-proxy, rate-sensitive sector — this checks whether that "
            "theory actually shows up as a real synthetic-control gap, using "
            "the other 10 sectors as donors, or whether XLU just moved with "
            "the broader market like everything else that week. (Substituted "
            "for a literal single-day 'AI-datacenter-power' event test since "
            "that theme doesn't have one clean, verifiable catalyst date — "
            "this is the more rigorously anchored version of 'is XLU moving "
            "for a distinct reason.')"
        ),
        "treated": "XLU",
        "donors": [t for t in SECTOR_ETFS if t != "XLU"],
        "treatment_date": "2026-06-17",
        "fit_end": "2026-02-15",
        "pre_start": "2024-06-17",
    },
    "sndk_supply_glut_fear": {
        "title": "Did SanDisk's Jul 2 supply-glut selloff break it from its memory-chip peers?",
        "description": (
            "Treated: SNDK. Donors: WDC, MU, STX, NTAP (memory/storage peers "
            "also riding the same 2026 AI-driven DRAM/NAND shortage supercycle "
            "narrative) — hand-picked, not algorithmic. Treatment date is "
            "2026-07-02, the day SNDK fell about 14% intraday (11% close to "
            "close per same-day reporting) on Samsung/SK Hynix new-supply and "
            "AI-capex-peak fears spreading across the whole memory complex. "
            "This was the largest of several repeated 'supply glut fear' "
            "selloffs in the group through Jul-Sep 2026 (further echoes hit "
            "on 7/13, 7/29, 8/6, 8/18, and 9/10) — 7/2 was chosen as the "
            "single cleanest, largest-magnitude catalyst date rather than "
            "trying to model the whole multi-month sequence at once. Tests "
            "whether SNDK's drop was company-specific or part of a shared "
            "sector re-pricing that should also show up in WDC/MU/STX/NTAP, "
            "against a backdrop where the underlying shortage thesis (DRAM/"
            "NAND contract prices up 58-75% QoQ in Q2 2026) stayed intact "
            "through the same window."
        ),
        "treated": "SNDK",
        "donors": ["WDC", "MU", "STX", "NTAP"],
        "treatment_date": "2026-07-02",
        "fit_end": "2026-07-02",
        "pre_start": "2026-01-02",
    },
}
