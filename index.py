"""Builds reports/index.html — a browsable list of every case study report,
newest first. Plain static files: regenerated on every
run.py invocation, not maintained by hand.
"""
from __future__ import annotations

import glob
import json
import os


# Fixed status palette (never themed, reserved for state — not reused for series color)
BADGE_COLORS = {
    "real-effect": "#0ca30c",     # good — a real, unit-specific effect found
    "no-effect": "#898781",       # neutral/muted — placebo-comparable, not distinct (not a "bad" state)
    "loose-fit": "#fab219",       # warning — usable but caveated
    "bad-fit": "#d03b3b",         # critical — don't trust the result at all
}

PAGE_TEMPLATE = """<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<title>Causal Toolkit — Case Studies</title>
<style>
  body {{
    margin:0; font-family: system-ui,-apple-system,"Segoe UI",sans-serif;
    background:#0d0d0d; color:#ffffff;
  }}
  .wrap {{ max-width: 760px; margin: 0 auto; padding: 40px 20px 60px; }}
  h1 {{ font-size: 22px; margin: 0 0 6px; }}
  .subtitle {{ color:#c3c2b7; font-size: 14px; margin-bottom: 32px; }}
  .card {{
    display:block; background:#1a1a19; border:1px solid rgba(255,255,255,0.10);
    border-radius:10px; padding:18px 22px; margin-bottom:14px; text-decoration:none;
    color:inherit;
  }}
  .card:hover {{ border-color: rgba(255,255,255,0.25); }}
  .card-top {{ display:flex; align-items:center; justify-content:space-between; gap:12px; }}
  .card-title {{ font-size: 16px; font-weight: 600; margin:0; }}
  .badge {{
    font-size:11px; text-transform:uppercase; letter-spacing:0.5px; font-weight:600;
    padding: 3px 9px; border-radius: 999px; white-space:nowrap;
  }}
  .card-desc {{ color:#c3c2b7; font-size: 13px; margin-top: 8px; line-height:1.5; }}
  .card-meta {{ color:#898781; font-size: 11px; margin-top: 10px; }}
  .empty {{ color:#898781; font-size: 14px; }}
  .footer {{ color:#898781; font-size: 11px; margin-top: 32px; }}
  h2.section-label {{
    font-size:12px; text-transform:uppercase; letter-spacing:0.6px; font-weight:600;
    color:#898781; margin:0 0 14px; padding-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.10);
  }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Causal Toolkit — Case Studies</h1>
  <div class="subtitle">Synthetic-control tests, newest first. Click through for the full
    chart, fit-quality check, placebo test, and verdict.</div>
  <h2 class="section-label">Case Studies</h2>
  {cards}
  <div class="footer">Regenerated automatically by run.py on every case-study run.</div>
</div>
</body>
</html>
"""


def _load_all_meta(reports_dir: str) -> list[dict]:
    metas = []
    for path in glob.glob(os.path.join(reports_dir, "*.meta.json")):
        with open(path, encoding="utf-8") as f:
            metas.append(json.load(f))
    metas.sort(key=lambda m: m.get("generated_at_iso", ""), reverse=True)
    return metas


def rebuild(reports_dir: str = "reports") -> str:
    metas = _load_all_meta(reports_dir)

    if not metas:
        cards_html = '<div class="empty">No case studies run yet.</div>'
    else:
        cards = []
        for m in metas:
            color = BADGE_COLORS.get(m["badge_class"], "#898781")
            cards.append(f"""
    <a class="card" href="{m['key']}.html">
      <div class="card-top">
        <span class="card-title">{m['title']}</span>
        <span class="badge" style="background:{color}22;color:{color};border:1px solid {color}55">
          {m['badge_label']}
        </span>
      </div>
      <div class="card-desc">{m['description']}</div>
      <div class="card-meta">Treated: {m['treated']} &middot; Generated {m['generated_at']}</div>
    </a>""")
        cards_html = "\n".join(cards)

    html = PAGE_TEMPLATE.format(cards=cards_html)
    out_path = os.path.join(reports_dir, "index.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


if __name__ == "__main__":
    print(f"wrote {rebuild()}")
