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
    "msft_earnings_record_pop": {
        "title": "Did MSFT's record Jul 30 earnings pop outpace fellow hyperscalers, or did the whole group re-rate?",
        "description": (
            "Treated: MSFT. Donors: GOOGL, META, AMZN (fellow Mag-7 "
            "hyperscalers, same donor logic as googl_capex_guidance) — hand-"
            "picked, not algorithmic. Treatment date is MSFT's Jul 30 after-"
            "close report: revenue +18% YoY to $90B, net income +31%, and "
            "guidance for ~45% constant-currency Azure growth (vs. a 40.92% "
            "estimate) — the stock closed up about 16%, adding nearly $450B "
            "in market value, the largest single-day market-cap gain on "
            "record for any company. This is the mirror case of "
            "googl_capex_guidance: that one tested whether GOOGL's post-"
            "guidance selloff eight days earlier (Jul 22) was company-"
            "specific or a shared re-pricing; this tests the same question "
            "on the opposite signal — a beat instead of a miss, in the same "
            "hyperscaler group within the same two-week window."
        ),
        "treated": "MSFT",
        "donors": ["GOOGL", "META", "AMZN"],
        "treatment_date": "2026-07-30",
        "fit_end": "2026-07-30",
        "pre_start": "2026-01-30",
    },
    "mu_meta_compute_chip_glut_fear": {
        "title": "Did Micron's Jul 1 'Meta Compute' selloff break it from fellow chip suppliers, or hit the whole group?",
        "description": (
            "Treated: MU. Donors: AMD, NVDA, INTC (AI/GPU-chip suppliers "
            "facing the same demand-destruction read) — hand-picked, not "
            "algorithmic. Treatment date is 2026-07-01: Meta announced 'Meta "
            "Compute,' a plan to resell its own excess AI infrastructure "
            "capacity, which the market read as evidence hyperscaler GPU "
            "demand may be peaking rather than perpetually scarce. Chip "
            "suppliers sold off hard the same day (MU -10.6%, AMD -6.9%, "
            "NVDA -1.25%, the Philadelphia Semiconductor Index down over 10% "
            "across the next two sessions), even as META itself rose about "
            "9% on its own announcement — a genuine divergence between the "
            "company making the move and the suppliers reading it as bad "
            "news. This is a different mechanism from sndk_supply_glut_fear "
            "(that one was about NAND/DRAM oversupply from Samsung/SK Hynix; "
            "this one is about AI-chip demand destruction from a hyperscaler "
            "reselling capacity instead of buying more). Tests whether MU's "
            "outsized drop was company-specific or the whole chip-supplier "
            "group re-priced together on the same news."
        ),
        "treated": "MU",
        "donors": ["AMD", "NVDA", "INTC"],
        "treatment_date": "2026-07-01",
        "fit_end": "2026-07-01",
        "pre_start": "2026-01-01",
    },
    "ntap_ai_quarter_beat": {
        "title": "Did NetApp's Sep 11 AI-driven earnings beat break it from its storage/memory peers?",
        "description": (
            "Treated: NTAP. Donors: WDC, MU, STX, SNDK (same storage/memory peer "
            "group as sndk_supply_glut_fear, with SNDK now a donor instead of a "
            "peer input and NTAP promoted to treated) — hand-picked, not "
            "algorithmic. Treatment date is NetApp's 2026-09-11 earnings report, "
            "an AI-driven beat that pushed the stock as much as +11% intraday "
            "before settling to a smaller close-to-close gain. This case was "
            "originally planned right after sndk_supply_glut_fear but shelved: "
            "as of that writing (a few days post-event) yfinance had zero "
            "trading days of post-treatment data, so the post-period gap "
            "computed as NaN. Revisited here with a full week of post-earnings "
            "data available. **Fails the fit-quality gate** (relative RMSE "
            "1.10x) — same outcome as sndk_supply_glut_fear (1.02x): this "
            "donor pool cannot reconstruct NTAP's own pre-period path either, "
            "so the post-period gap isn't trustworthy in either direction. "
            "Shipped as an honest negative result rather than swapped for a "
            "better-fitting pool to force a cleaner-looking answer."
        ),
        "treated": "NTAP",
        "donors": ["WDC", "MU", "STX", "SNDK"],
        "treatment_date": "2026-09-11",
        "fit_end": "2026-09-11",
        "pre_start": "2026-03-11",
    },
}
