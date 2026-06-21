#!/usr/bin/env python3
"""
TSA Feedback PDF — essay + blunt teacher feedback, side by side, one essay per page.
No scores, no extraction. Just the essay and what the model said about it.
"""
import json, time
from pathlib import Path
from weasyprint import HTML

DATA_DIR = Path(__file__).resolve().parent / "guardrails"
ESSAYS_PATH = DATA_DIR / "essays.json"
FEEDBACK_PATH = DATA_DIR / "feedback_audit.json"
OUTPUT_PATH = DATA_DIR / "tsa_feedback_report.pdf"

CSS = """
@page {
    size: letter landscape;
    margin: 0.5in;
    @bottom-center {
        content: "TSA Feedback Report — page " counter(page) " of " counter(pages);
        font-size: 8pt;
        color: #999;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
}
body {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 9pt;
    line-height: 1.45;
    color: #222;
}
h1 {
    font-size: 20pt;
    margin: 0 0 4pt 0;
    color: #111;
}
h2 {
    font-size: 12pt;
    margin: 0 0 6pt 0;
    padding-bottom: 4pt;
    border-bottom: 2px solid #444;
    color: #333;
}
.meta {
    font-size: 8pt;
    color: #888;
    margin-bottom: 14pt;
}
.page-break {
    page-break-before: always;
}
.columns {
    display: flex;
    gap: 20px;
    height: 100%;
}
.col {
    flex: 1;
    min-width: 0;
}
.col-left {
    border-right: 1px dashed #ccc;
    padding-right: 18px;
}
.col-right {
    padding-left: 2px;
}
.essay-text {
    white-space: pre-wrap;
    font-size: 9pt;
    background: #f9f9f9;
    padding: 10pt;
    border-radius: 4pt;
    border: 1px solid #e0e0e0;
}
.feedback-text {
    white-space: pre-wrap;
    font-size: 9pt;
    background: #fffdf5;
    padding: 10pt;
    border-radius: 4pt;
    border: 1px solid #e8e0c0;
}
.label {
    font-size: 7.5pt;
    text-transform: uppercase;
    letter-spacing: 1.2pt;
    color: #666;
    margin-bottom: 6pt;
    font-weight: 700;
}
.badge {
    display: inline-block;
    font-size: 7pt;
    font-weight: 700;
    padding: 2pt 8pt;
    border-radius: 3pt;
    margin-right: 6pt;
    color: #fff;
}
.badge-below  { background: #c0392b; }
.badge-basic  { background: #e67e22; }
.badge-prof   { background: #2980b9; }
.badge-adv    { background: #27ae60; }
.title-bar {
    text-align: center;
    padding: 30pt 0 10pt 0;
}
.title-bar h1 {
    font-size: 26pt;
    letter-spacing: 1pt;
}
.title-bar .sub {
    font-size: 10pt;
    color: #777;
    margin-top: 6pt;
}
"""

def level_badge_class(level):
    l = level.lower()
    if "below" in l: return "badge-below"
    if "basic" in l: return "badge-basic"
    if "prof" in l: return "badge-prof"
    if "adv" in l: return "badge-adv"
    return "badge-basic"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build_html(essays, feedback_map):
    parts = []
    # Title page
    parts.append(f"""
    <div class="title-bar">
        <h1>📝 TSA Feedback Report</h1>
        <div class="sub">Teacher Scoring Assistant — gemma4:26b (Lenovo CUDA)</div>
        <div class="sub">Generated {time.strftime('%B %d, %Y at %H:%M')}</div>
        <div class="sub">{len(essays)} essays — feedback only, no scores</div>
    </div>
    """)

    for i, essay in enumerate(essays):
        eid = essay["id"]
        level = essay["level"]
        score = essay["score"]
        text = essay["text"]
        fb = feedback_map.get(eid, "[no feedback available]")

        badge_cls = level_badge_class(level)

        parts.append(f"""
        <div class="page-break"></div>
        <h2>Essay {i+1} of {len(essays)}</h2>
        <div class="meta">
            <span class="badge {badge_cls}">{level}</span>
            ID: {esc(eid)} · Human score: {score}/12 · Essay: {len(text.split())} words · Feedback: {len(fb.split())} words
        </div>
        <div class="columns">
            <div class="col col-left">
                <div class="label">📄 Student Essay</div>
                <div class="essay-text">{esc(text)}</div>
            </div>
            <div class="col col-right">
                <div class="label">💬 Teacher Feedback</div>
                <div class="feedback-text">{esc(fb)}</div>
            </div>
        </div>
        """)

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body>{"".join(parts)}</body></html>"""

def main():
    with open(ESSAYS_PATH) as f:
        essays = json.load(f)["essays"]
    with open(FEEDBACK_PATH) as f:
        feedback_data = json.load(f)["results"]
    feedback_map = {r["id"]: r["feedback"] for r in feedback_data}

    html = build_html(essays, feedback_map)
    HTML(string=html).write_pdf(str(OUTPUT_PATH))
    print(f"✅ PDF saved: {OUTPUT_PATH}")
    print(f"   {len(essays)} essays × feedback = {len(essays)} pages + title")

if __name__ == "__main__":
    main()
