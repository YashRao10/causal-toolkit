"""Renders a synthetic-control case study into a self-contained HTML report:
an SVG line chart (actual vs. synthetic, treatment date marked) plus a
fit-quality summary, the placebo-test table, and a written verdict.

No external dependencies (no CDN, no JS libraries) — matches the rest of
this user's local HTML reports (e.g. portfolio_dashboard.html).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

CHART_W, CHART_H = 860, 380
MARGIN = {"top": 24, "right": 76, "bottom": 40, "left": 56}


def _scale_x(dates: pd.DatetimeIndex, plot_w: float) -> dict:
    t0, t1 = dates[0].value, dates[-1].value
    span = max(t1 - t0, 1)
    return {str(d.date()): MARGIN["left"] + (d.value - t0) / span * plot_w for d in dates}


def _path(dates: pd.DatetimeIndex, values: np.ndarray, xscale: dict, yscale) -> str:
    pts = [f"{xscale[str(d.date())]:.2f},{yscale(v):.2f}" for d, v in zip(dates, values)]
    return "M" + " L".join(pts)


def _build_chart(effect_df: pd.DataFrame, treatment_date: str, fit_end: str) -> str:
    plot_w = CHART_W - MARGIN["left"] - MARGIN["right"]
    plot_h = CHART_H - MARGIN["top"] - MARGIN["bottom"]

    y_min = min(effect_df["actual"].min(), effect_df["synthetic"].min())
    y_max = max(effect_df["actual"].max(), effect_df["synthetic"].max())
    pad = (y_max - y_min) * 0.08 or 1.0
    y_min, y_max = y_min - pad, y_max + pad

    def yscale(v):
        return MARGIN["top"] + (1 - (v - y_min) / (y_max - y_min)) * plot_h

    xscale = _scale_x(effect_df.index, plot_w)

    actual_path = _path(effect_df.index, effect_df["actual"].values, xscale, yscale)
    synth_path = _path(effect_df.index, effect_df["synthetic"].values, xscale, yscale)

    # Gridlines: 4 horizontal steps
    gridlines = []
    for i in range(5):
        v = y_min + (y_max - y_min) * i / 4
        y = yscale(v)
        gridlines.append(
            f'<line class="gridline" x1="{MARGIN["left"]}" y1="{y:.1f}" '
            f'x2="{CHART_W - MARGIN["right"]}" y2="{y:.1f}"/>'
            f'<text class="tick" x="{MARGIN["left"] - 8}" y="{y:.1f}" '
            f'text-anchor="end" dominant-baseline="middle">{v:.0f}</text>'
        )

    treat_x = xscale.get(str(pd.Timestamp(treatment_date).date()))
    fit_end_x = xscale.get(str(pd.Timestamp(fit_end).date()))

    confound_rect = ""
    if fit_end_x is not None and treat_x is not None and fit_end_x < treat_x:
        confound_rect = (
            f'<rect class="confound-band" x="{fit_end_x:.1f}" y="{MARGIN["top"]}" '
            f'width="{treat_x - fit_end_x:.1f}" height="{plot_h}"/>'
        )

    treatment_line = ""
    if treat_x is not None:
        treatment_line = (
            f'<line class="treatment-line" x1="{treat_x:.1f}" y1="{MARGIN["top"]}" '
            f'x2="{treat_x:.1f}" y2="{MARGIN["top"] + plot_h}"/>'
            f'<text class="treatment-label" x="{treat_x:.1f}" y="{MARGIN["top"] - 8}" '
            f'text-anchor="middle">Treatment date</text>'
        )

    last = effect_df.iloc[-1]
    last_x = xscale[str(effect_df.index[-1].date())]
    actual_label_y = yscale(last["actual"])
    synth_label_y = yscale(last["synthetic"])
    # nudge apart if too close (avoid collision per marks-and-anatomy.md)
    if abs(actual_label_y - synth_label_y) < 14:
        if actual_label_y < synth_label_y:
            actual_label_y -= 7
            synth_label_y += 7
        else:
            actual_label_y += 7
            synth_label_y -= 7

    # Hover hit-data embedded for the JS crosshair layer
    hover_data = [
        {
            "x": round(xscale[str(d.date())], 2),
            "date": d.strftime("%b %d, %Y").replace(" 0", " ") if hasattr(d, "strftime") else str(d),
            "actual": round(float(a), 2),
            "synthetic": round(float(s), 2),
            "gap": round(float(g), 2),
        }
        for d, a, s, g in zip(
            effect_df.index, effect_df["actual"], effect_df["synthetic"], effect_df["gap"]
        )
    ]

    svg = f"""
<div class="viz-root">
  <svg viewBox="0 0 {CHART_W} {CHART_H}" width="100%" height="{CHART_H}" id="chart-svg">
    {confound_rect}
    {"".join(gridlines)}
    <line class="axis" x1="{MARGIN["left"]}" y1="{MARGIN["top"] + plot_h}"
          x2="{CHART_W - MARGIN["right"]}" y2="{MARGIN["top"] + plot_h}"/>
    {treatment_line}
    <path class="line-synth" d="{synth_path}" fill="none"/>
    <path class="line-actual" d="{actual_path}" fill="none"/>
    <circle class="end-dot dot-actual" cx="{last_x:.1f}" cy="{yscale(last['actual']):.1f}" r="4"/>
    <circle class="end-dot dot-synth" cx="{last_x:.1f}" cy="{yscale(last['synthetic']):.1f}" r="4"/>
    <text class="end-label label-actual" x="{last_x + 8:.1f}" y="{actual_label_y:.1f}"
          dominant-baseline="middle">Actual</text>
    <text class="end-label label-synth" x="{last_x + 8:.1f}" y="{synth_label_y:.1f}"
          dominant-baseline="middle">Synthetic</text>
    <line class="crosshair" id="crosshair" x1="0" y1="{MARGIN["top"]}" x2="0"
          y2="{MARGIN["top"] + plot_h}" style="display:none"/>
    <rect class="hover-capture" x="{MARGIN["left"]}" y="{MARGIN["top"]}"
          width="{plot_w}" height="{plot_h}" fill="transparent"
          onmousemove="onChartHover(event)" onmouseleave="onChartLeave()"/>
  </svg>
  <div class="legend">
    <span class="legend-item"><span class="swatch swatch-actual"></span>Actual</span>
    <span class="legend-item"><span class="swatch swatch-synth"></span>Synthetic (counterfactual)</span>
  </div>
  <div class="tooltip" id="chart-tooltip" style="display:none"></div>
</div>
<script>
  const HOVER_DATA_XXSAFEIDXX = {json.dumps(hover_data)};
</script>
"""
    return svg


def _placebo_table(placebo_df: pd.DataFrame, treated: str) -> str:
    rows = []
    for _, r in placebo_df.iterrows():
        cls = "row-treated" if r["is_treated"] else ""
        rows.append(
            f'<tr class="{cls}"><td>{r["unit"]}{" (treated)" if r["is_treated"] else ""}</td>'
            f'<td class="num">{r["mean_post_gap_pct"]:+.2f}%</td>'
            f'<td class="num">{r["max_abs_post_gap_pct"]:.2f}%</td></tr>'
        )
    return f"""
<table class="placebo-table">
  <thead><tr><th>Unit</th><th>Mean post-period gap</th><th>Max abs. gap</th></tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
"""


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
  /* Dark is the unconditional default look for this report (not OS-driven) —
     light is available only via an explicit data-theme="light" override. */
  :root {{ color-scheme: dark; }}
  body {{
    margin:0; font-family: system-ui,-apple-system,"Segoe UI",sans-serif;
    background:#0d0d0d; color:#ffffff;
  }}
  :root[data-theme="light"] body {{ background:#f9f9f7; color:#0b0b0b; }}

  .wrap {{ max-width: 920px; margin: 0 auto; padding: 32px 20px 60px; }}
  h1 {{ font-size: 22px; margin: 0 0 6px; }}
  .subtitle {{ color:#c3c2b7; font-size: 14px; margin-bottom: 24px; }}
  :root[data-theme="light"] .subtitle {{ color:#52514e; }}

  .card {{
    background:#1a1a19; border:1px solid rgba(255,255,255,0.10); border-radius:10px;
    padding:20px 24px; margin-bottom:20px;
  }}
  :root[data-theme="light"] .card {{ background:#fcfcfb; border-color: rgba(11,11,11,0.10); }}

  .card h2 {{ font-size: 15px; text-transform: uppercase; letter-spacing: 0.5px;
    color:#c3c2b7; margin: 0 0 14px; }}
  :root[data-theme="light"] .card h2 {{ color:#52514e; }}

  .viz-root {{
    --surface-1:#1a1a19; --text-primary:#ffffff; --text-secondary:#c3c2b7;
    --text-muted:#898781; --grid:#2c2c2a; --baseline:#383835;
    --series-1:#3987e5; --series-2:#d95926;
  }}
  :root[data-theme="light"] .viz-root {{
    --surface-1:#fcfcfb; --text-primary:#0b0b0b; --text-secondary:#52514e;
    --text-muted:#898781; --grid:#e1e0d9; --baseline:#c3c2b7;
    --series-1:#2a78d6; --series-2:#eb6834;
  }}

  .gridline {{ stroke: var(--grid); stroke-width: 1; }}
  .axis {{ stroke: var(--baseline); stroke-width: 1; }}
  .tick {{ fill: var(--text-muted); font-size: 11px; }}
  .line-actual {{ stroke: var(--series-1); stroke-width: 2; }}
  .line-synth {{ stroke: var(--series-2); stroke-width: 2; }}
  .end-dot {{ stroke: var(--surface-1); stroke-width: 2; }}
  .dot-actual {{ fill: var(--series-1); }}
  .dot-synth {{ fill: var(--series-2); }}
  .end-label {{ font-size: 12px; fill: var(--text-secondary); }}
  .treatment-line {{ stroke: var(--text-muted); stroke-width: 1; stroke-dasharray: 3 3; }}
  .treatment-label {{ font-size: 11px; fill: var(--text-muted); }}
  .confound-band {{ fill: var(--text-muted); opacity: 0.08; }}
  .crosshair {{ stroke: var(--text-muted); stroke-width: 1; pointer-events:none; }}

  .legend {{ display:flex; gap:18px; padding: 6px 0 0 56px; font-size: 13px;
    color: var(--text-secondary); }}
  .legend-item {{ display:flex; align-items:center; gap:6px; }}
  .swatch {{ width:10px; height:10px; border-radius:2px; display:inline-block; }}
  .swatch-actual {{ background: var(--series-1); }}
  .swatch-synth {{ background: var(--series-2); }}

  .tooltip {{
    position:absolute; background: var(--surface-1); border:1px solid rgba(255,255,255,0.10);
    border-radius:6px; padding:8px 10px; font-size:12px; pointer-events:none;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4); color: var(--text-primary);
  }}
  :root[data-theme="light"] .tooltip {{
    border-color: rgba(11,11,11,0.10); box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  }}
  .tooltip .t-date {{ color: var(--text-secondary); margin-bottom:4px; }}
  .tooltip .t-row {{ display:flex; justify-content:space-between; gap:16px; }}

  table.placebo-table {{ width:100%; border-collapse: collapse; font-size: 13px; }}
  table.placebo-table th, table.placebo-table td {{
    padding: 7px 10px; text-align:left; border-bottom: 1px solid #2c2c2a;
    font-variant-numeric: tabular-nums; color: inherit;
  }}
  :root[data-theme="light"] table.placebo-table th,
  :root[data-theme="light"] table.placebo-table td {{ border-bottom-color: #e1e0d9; }}
  table.placebo-table td.num {{ text-align: right; }}
  table.placebo-table th {{ color:#898781; font-size:11px; text-transform:uppercase;
    letter-spacing:0.5px; }}
  tr.row-treated {{ font-weight: 600; }}

  .verdict {{ font-size: 14px; line-height: 1.6; }}
  .kv {{ display:grid; grid-template-columns: 1fr 1fr; gap: 10px 24px; font-size: 13px; }}
  .kv div span.k {{ color:#c3c2b7; display:block; font-size:11px;
    text-transform:uppercase; letter-spacing:0.5px; }}
  :root[data-theme="light"] .kv div span.k {{ color:#52514e; }}

  .footer {{ color:#898781; font-size: 11px; margin-top: 32px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>{title}</h1>
  <div class="subtitle">{description}</div>

  <div class="card">
    <h2>Actual vs. synthetic counterfactual</h2>
    {chart}
  </div>

  <div class="card">
    <h2>Fit quality</h2>
    <div class="kv">
      <div><span class="k">Fit-window RMSE</span>{fit_rmse}</div>
      <div><span class="k">RMSE &divide; fit-window std dev</span>{relative_rmse}&times;</div>
      <div><span class="k">Fit-window days</span>{fit_days}</div>
      <div><span class="k">Confound-window mean gap</span>{confound_gap}</div>
      <div><span class="k">Post-period mean gap</span>{post_gap}</div>
    </div>
  </div>

  <div class="card">
    <h2>Placebo test — same method run on every unit, treated one highlighted</h2>
    {placebo_table}
  </div>

  <div class="card">
    <h2>Verdict</h2>
    <div class="verdict">{verdict}</div>
  </div>

  <div class="footer">Generated {generated_at} &middot; causal-toolkit &middot; synthetic control
    (Abadie-Diamond-Hainmueller, outcome-only variant) &middot; donor pool hand-picked, not
    algorithmically matched &middot; treat every result here as directional, not a p-value.</div>
</div>
<script>
function onChartHover(evt) {{
  const svg = document.getElementById('chart-svg');
  const pt = svg.createSVGPoint();
  pt.x = evt.clientX; pt.y = evt.clientY;
  const loc = pt.matrixTransform(svg.getScreenCTM().inverse());
  const data = window.__HOVER_DATA__;
  if (!data || !data.length) return;
  let nearest = data[0], minDist = Infinity;
  for (const d of data) {{
    const dist = Math.abs(d.x - loc.x);
    if (dist < minDist) {{ minDist = dist; nearest = d; }}
  }}
  const crosshair = document.getElementById('crosshair');
  crosshair.setAttribute('x1', nearest.x); crosshair.setAttribute('x2', nearest.x);
  crosshair.style.display = 'block';
  const tip = document.getElementById('chart-tooltip');
  tip.style.display = 'block';
  tip.style.left = (evt.pageX + 14) + 'px';
  tip.style.top = (evt.pageY - 40) + 'px';
  tip.innerHTML = `<div class="t-date">${{nearest.date}}</div>` +
    `<div class="t-row"><span>Actual</span><strong>${{nearest.actual.toFixed(2)}}</strong></div>` +
    `<div class="t-row"><span>Synthetic</span><strong>${{nearest.synthetic.toFixed(2)}}</strong></div>` +
    `<div class="t-row"><span>Gap</span><strong>${{nearest.gap >= 0 ? '+' : ''}}${{nearest.gap.toFixed(2)}}</strong></div>`;
}}
function onChartLeave() {{
  document.getElementById('crosshair').style.display = 'none';
  document.getElementById('chart-tooltip').style.display = 'none';
}}
</script>
</body>
</html>
"""


def render(
    case_key: str,
    config: dict,
    effect_df: pd.DataFrame,
    fit_quality: dict,
    placebo_df: pd.DataFrame,
    verdict: str,
    generated_at: str,
    relative_rmse: float = 0.0,
) -> str:
    chart_html = _build_chart(effect_df, config["treatment_date"], config["fit_end"]).replace(
        "XXSAFEIDXX", case_key
    )
    # inline the hover data global (the chart embeds a per-case JS const;
    # point window.__HOVER_DATA__ at it so the shared onChartHover() can find it)
    chart_html += f"<script>window.__HOVER_DATA__ = HOVER_DATA_{case_key};</script>"

    confound = effect_df[effect_df.get("segment", effect_df["period"]) == "confound"] \
        if "segment" in effect_df.columns else effect_df.iloc[0:0]
    post = effect_df[effect_df.get("segment", effect_df["period"]).isin(["post"])]

    return PAGE_TEMPLATE.format(
        title=config["title"],
        description=config["description"],
        chart=chart_html,
        fit_rmse=fit_quality.get("rmse", fit_quality.get("pre_rmse")),
        relative_rmse=f"{relative_rmse:.2f}",
        fit_days=fit_quality.get("n_periods", fit_quality.get("n_pre_periods")),
        confound_gap=f"{confound['gap'].mean():+.2f}" if len(confound) else "n/a (fit-end = treatment date)",
        post_gap=f"{post['gap'].mean():+.2f}",
        placebo_table=_placebo_table(placebo_df, config["treated"]),
        verdict=verdict,
        generated_at=generated_at,
    )
