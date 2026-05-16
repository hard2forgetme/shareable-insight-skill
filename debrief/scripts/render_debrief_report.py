#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path


def esc(value):
    return html.escape("" if value is None else str(value))


def rich_text(text):
    if not text:
        return ""
    parts = []
    for para in str(text).strip().split("\n\n"):
        para = esc(para).replace("**", "\u0000")
        segs = para.split("\u0000")
        rebuilt = []
        for idx, seg in enumerate(segs):
            rebuilt.append(f"<strong>{seg}</strong>" if idx % 2 else seg)
        parts.append("<p>" + "<br>".join("".join(rebuilt).splitlines()) + "</p>")
    return "\n".join(parts)


def stat_cards(stats):
    if not stats:
        return ""
    cards = []
    for stat in stats:
        cards.append(
            f"""
            <div class="stat">
              <div class="stat-value">{esc(stat.get('value', ''))}</div>
              <div class="stat-label">{esc(stat.get('label', ''))}</div>
            </div>
            """
        )
    return '<section class="stats">' + "".join(cards) + "</section>"


def at_a_glance(items):
    if not items:
        return ""
    rendered = []
    for item in items:
        link = ""
        if item.get("link_text") and item.get("link_href"):
            link = f' <a href="{esc(item["link_href"])}">{esc(item["link_text"])}</a>'
        rendered.append(
            f"""
            <div class="glance-item">
              <h3>{esc(item.get('title', ''))}</h3>
              <div>{rich_text(item.get('body', ''))}{link}</div>
            </div>
            """
        )
    return '<section class="hero"><h2>At a Glance</h2>' + "".join(rendered) + "</section>"


def work_areas(items):
    if not items:
        return ""
    cards = []
    for area in items:
        count = area.get("session_count")
        badge = f'<span class="badge">~{esc(count)} sessions</span>' if count is not None else ""
        cards.append(
            f"""
            <article class="card area-card">
              <div class="row">
                <h3>{esc(area.get('name', ''))}</h3>
                {badge}
              </div>
              <p>{esc(area.get('description', ''))}</p>
            </article>
            """
        )
    return '<section id="work"><h2>What You Work On</h2><div class="stack">' + "".join(cards) + "</div></section>"


def interaction_style(section):
    if not section:
        return ""
    key = ""
    if section.get("key_pattern"):
        key = f'<div class="key-pattern"><strong>Key pattern:</strong> {esc(section["key_pattern"])}</div>'
    return (
        '<section id="style"><h2>How You Use the Agent</h2><div class="card prose">'
        + rich_text(section.get("narrative", ""))
        + key
        + "</div></section>"
    )


def simple_items(section_id, title, data, tone):
    if not data or not data.get("items"):
        return ""
    intro = f'<p class="section-intro">{esc(data.get("intro", ""))}</p>' if data.get("intro") else ""
    cards = []
    for item in data["items"]:
        cards.append(
            f"""
            <article class="card {tone}">
              <h3>{esc(item.get('title', ''))}</h3>
              <p>{esc(item.get('description', ''))}</p>
            </article>
            """
        )
    return f'<section id="{section_id}"><h2>{esc(title)}</h2>{intro}<div class="stack">{"".join(cards)}</div></section>'


def friction_section(data):
    if not data or not data.get("categories"):
        return ""
    intro = f'<p class="section-intro">{esc(data.get("intro", ""))}</p>' if data.get("intro") else ""
    cards = []
    for cat in data["categories"]:
        examples = ""
        if cat.get("examples"):
            lis = "".join(f"<li>{esc(example)}</li>" for example in cat["examples"])
            examples = f"<ul>{lis}</ul>"
        cards.append(
            f"""
            <article class="card friction">
              <h3>{esc(cat.get('category', ''))}</h3>
              <p>{esc(cat.get('description', ''))}</p>
              {examples}
            </article>
            """
        )
    return f'<section id="friction"><h2>Where Things Go Wrong</h2>{intro}<div class="stack">{"".join(cards)}</div></section>'


def additions_section(items):
    if not items:
        return ""
    cards = []
    for item in items:
        scaffold = ""
        if item.get("prompt_scaffold"):
            scaffold = f'<div class="small-label">{esc(item["prompt_scaffold"])}</div>'
        cards.append(
            f"""
            <article class="card addition">
              {scaffold}
              <pre>{esc(item.get('addition', ''))}</pre>
              <p>{esc(item.get('why', ''))}</p>
            </article>
            """
        )
    return '<section id="additions"><h2>Suggested Instruction Additions</h2><div class="stack">' + "".join(cards) + "</div></section>"


def feature_cards(items, section_id, title):
    if not items:
        return ""
    cards = []
    for item in items:
        code = ""
        if item.get("example_code"):
            code = f'<pre>{esc(item["example_code"])}</pre>'
        extra = ""
        if item.get("detail"):
            extra = f"<p>{esc(item['detail'])}</p>"
        cards.append(
            f"""
            <article class="card feature">
              <h3>{esc(item.get('feature') or item.get('title') or '')}</h3>
              <p class="lede">{esc(item.get('one_liner') or item.get('suggestion') or '')}</p>
              <p>{esc(item.get('why_for_you') or item.get('whats_possible') or '')}</p>
              {extra}
              {code}
            </article>
            """
        )
    return f'<section id="{section_id}"><h2>{esc(title)}</h2><div class="stack">{"".join(cards)}</div></section>'


def patterns_section(items):
    if not items:
        return ""
    cards = []
    for item in items:
        prompt = ""
        if item.get("copyable_prompt"):
            prompt = f'<div class="prompt-block"><div class="small-label">Copyable prompt</div><pre>{esc(item["copyable_prompt"])}</pre></div>'
        cards.append(
            f"""
            <article class="card pattern">
              <h3>{esc(item.get('title', ''))}</h3>
              <p class="lede">{esc(item.get('suggestion', ''))}</p>
              <p>{esc(item.get('detail', ''))}</p>
              {prompt}
            </article>
            """
        )
    return '<section id="patterns"><h2>New Usage Patterns</h2><div class="stack">' + "".join(cards) + "</div></section>"


def horizon_section(data):
    if not data or not data.get("opportunities"):
        return ""
    intro = f'<p class="section-intro">{esc(data.get("intro", ""))}</p>' if data.get("intro") else ""
    cards = []
    for item in data["opportunities"]:
        how = f'<p><strong>How to try:</strong> {esc(item.get("how_to_try", ""))}</p>' if item.get("how_to_try") else ""
        prompt = f'<div class="prompt-block"><div class="small-label">Copyable prompt</div><pre>{esc(item.get("copyable_prompt", ""))}</pre></div>' if item.get("copyable_prompt") else ""
        cards.append(
            f"""
            <article class="card horizon">
              <h3>{esc(item.get('title', ''))}</h3>
              <p>{esc(item.get('whats_possible', ''))}</p>
              {how}
              {prompt}
            </article>
            """
        )
    return f'<section id="horizon"><h2>On the Horizon</h2>{intro}<div class="stack">{"".join(cards)}</div></section>'


def charts_section(charts):
    if not charts:
        return ""
    blocks = []
    for chart in charts:
        bars = chart.get("bars") or []
        max_value = max((bar.get("value", 0) for bar in bars), default=1) or 1
        bar_html = []
        for bar in bars:
            width = (float(bar.get("value", 0)) / max_value) * 100.0
            color = esc(bar.get("color", "#2563eb"))
            bar_html.append(
                f"""
                <div class="bar-row">
                  <div class="bar-label">{esc(bar.get('label', ''))}</div>
                  <div class="bar-track"><div class="bar-fill" style="width:{width:.2f}%;background:{color}"></div></div>
                  <div class="bar-value">{esc(bar.get('value', ''))}</div>
                </div>
                """
            )
        blocks.append(f'<div class="card chart"><h3>{esc(chart.get("title", ""))}</h3>{"".join(bar_html)}</div>')
    return '<section id="charts"><h2>Signal Snapshot</h2><div class="grid-two">' + "".join(blocks) + "</div></section>"


def fun_ending(data):
    if not data or not data.get("headline"):
        return ""
    detail = f'<div class="fun-detail">{esc(data.get("detail", ""))}</div>' if data.get("detail") else ""
    return f'<section class="fun-ending"><div class="fun-headline">"{esc(data["headline"])}"</div>{detail}</section>'


def render(data):
    title = data.get("title", "Debrief Report")
    subtitle = data.get("subtitle", "")
    generated_at = data.get("generated_at", "")
    subject = data.get("subject", "")
    subtitle_bits = [bit for bit in [subtitle, subject, generated_at] if bit]
    subtitle_line = " | ".join(subtitle_bits)
    theme = data.get("theme", "default")
    is_mythos = theme == "mythos"

    nav_items = [
        ("work", "Work Areas", bool(data.get("work_areas"))),
        ("charts", "Signals", bool(data.get("charts"))),
        ("style", "Interaction", bool(data.get("interaction_style"))),
        ("wins", "Wins", bool(data.get("wins"))),
        ("friction", "Friction", bool(data.get("friction"))),
        ("additions", "Instructions", bool(data.get("claude_md_additions"))),
        ("features", "Features", bool(data.get("features"))),
        ("patterns", "Patterns", bool(data.get("patterns"))),
        ("horizon", "Horizon", bool(data.get("horizon"))),
    ]
    nav_html = "".join(
        f'<a href="#{section_id}">{label}</a>'
        for section_id, label, enabled in nav_items
        if enabled
    )

    sections = [
        stat_cards(data.get("stats")),
        at_a_glance(data.get("at_a_glance")),
        work_areas(data.get("work_areas")),
        charts_section(data.get("charts")),
        interaction_style(data.get("interaction_style")),
        simple_items("wins", "Impressive Things You Did", data.get("wins"), "win"),
        friction_section(data.get("friction")),
        additions_section(data.get("claude_md_additions")),
        feature_cards(data.get("features"), "features", "Existing Features to Try"),
        patterns_section(data.get("patterns")),
        horizon_section(data.get("horizon")),
        fun_ending(data.get("fun_ending")),
    ]

    css = f"""
    :root {{
      --bg: {"#0f1217" if is_mythos else "#f4efe7"};
      --paper: {"rgba(20, 25, 34, 0.84)" if is_mythos else "rgba(255, 250, 244, 0.88)"};
      --ink: {"#edf2f7" if is_mythos else "#1f2430"};
      --muted: {"#98a5b3" if is_mythos else "#626a77"};
      --line: {"rgba(125, 211, 252, 0.12)" if is_mythos else "rgba(74, 57, 38, 0.12)"};
      --moss: {"#10353a" if is_mythos else "#dde7cf"};
      --shadow: {"0 22px 60px rgba(0, 0, 0, 0.35)" if is_mythos else "0 18px 48px rgba(54, 38, 17, 0.08)"};
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Inter", "Avenir Next", -apple-system, BlinkMacSystemFont, sans-serif;
      color: var(--ink);
      background:
        {"radial-gradient(circle at top left, rgba(251,191,36,0.14), transparent 20%), radial-gradient(circle at 85% 8%, rgba(94,234,212,0.10), transparent 22%), radial-gradient(circle at 50% 75%, rgba(59,130,246,0.10), transparent 28%), linear-gradient(180deg, #0b0e13 0%, #0e131a 45%, var(--bg) 100%)" if is_mythos else "radial-gradient(circle at top left, rgba(200,156,39,0.18), transparent 22%), radial-gradient(circle at 85% 10%, rgba(86,99,71,0.14), transparent 24%), radial-gradient(circle at 40% 80%, rgba(183,110,69,0.10), transparent 30%), linear-gradient(180deg, #fbf6ef 0%, #f7f0e7 45%, var(--bg) 100%)"};
      line-height: 1.6;
    }}
    .wrap {{ max-width: 1120px; margin: 0 auto; padding: 40px 20px 96px; }}
    header {{
      position: relative;
      margin-bottom: 24px;
      padding: 26px 28px 22px;
      background: {"linear-gradient(135deg, rgba(15,22,30,0.88), rgba(20,28,38,0.94))" if is_mythos else "linear-gradient(135deg, rgba(255,252,248,0.82), rgba(248,240,228,0.92))"};
      border: 1px solid var(--line);
      border-radius: 30px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    header:before {{
      content: "";
      position: absolute;
      inset: 0;
      background:
        {"linear-gradient(120deg, rgba(251,191,36,0.12), transparent 30%), linear-gradient(300deg, rgba(94,234,212,0.10), transparent 35%)" if is_mythos else "linear-gradient(120deg, rgba(200,156,39,0.10), transparent 30%), linear-gradient(300deg, rgba(86,99,71,0.10), transparent 35%)"};
      pointer-events: none;
    }}
    .eyebrow {{
      position: relative;
      display: inline-block;
      margin-bottom: 12px;
      padding: 6px 10px;
      border-radius: 999px;
      background: {"rgba(251,191,36,0.14)" if is_mythos else "rgba(255, 244, 221, 0.9)"};
      color: {"#ffd166" if is_mythos else "#7f5a00"};
      font-size: 11px;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      font-weight: 700;
    }}
    h1 {{
      position: relative;
      margin: 0 0 8px;
      font-size: clamp(34px, 6vw, 58px);
      line-height: 0.96;
      max-width: 12ch;
      letter-spacing: -0.04em;
    }}
    .subtitle {{ position: relative; color: var(--muted); font-size: 14px; max-width: 70ch; }}
    .top-grid {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
      align-items: start;
      margin-bottom: 28px;
    }}
    .nav-card {{
      padding: 18px;
      background: {"rgba(16, 21, 28, 0.78)" if is_mythos else "rgba(255, 251, 246, 0.76)"};
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
      position: sticky;
      top: 20px;
    }}
    .nav-card h2 {{
      margin: 0 0 12px;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    .nav-links {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .nav-links a {{
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: {"rgba(255,255,255,0.04)" if is_mythos else "rgba(31, 36, 48, 0.04)"};
      border: 1px solid {"rgba(255,255,255,0.07)" if is_mythos else "rgba(31, 36, 48, 0.06)"};
      color: {"#c7d2de" if is_mythos else "#4f5661"};
      font-size: 13px;
    }}
    .nav-links a:hover {{
      background: {"rgba(251,191,36,0.12)" if is_mythos else "rgba(200, 156, 39, 0.10)"};
      border-color: {"rgba(251,191,36,0.26)" if is_mythos else "rgba(200, 156, 39, 0.25)"};
      text-decoration: none;
    }}
    h2 {{ margin: 44px 0 14px; font-size: 28px; letter-spacing: -0.03em; }}
    h3 {{ margin: 0 0 8px; font-size: 17px; }}
    p {{ margin: 0 0 10px; }}
    a {{ color: {"#ffd166" if is_mythos else "#8a5a00"}; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
      gap: 12px;
      margin: 26px 0;
    }}
    .stat, .card, .hero {{
      background: var(--paper);
      backdrop-filter: blur(6px);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: var(--shadow);
    }}
    .stat {{ padding: 18px 14px; text-align: center; }}
    .stat-value {{ font-size: 28px; font-weight: 800; letter-spacing: -0.04em; }}
    .stat-label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .hero {{
      padding: 24px;
      background: {"linear-gradient(135deg, rgba(47,29,13,0.96) 0%, rgba(24,34,41,0.98) 45%, rgba(12,41,37,0.96) 100%)" if is_mythos else "linear-gradient(135deg, rgba(255, 240, 208, 0.96) 0%, rgba(255, 251, 242, 0.96) 45%, rgba(237, 247, 231, 0.98) 100%)"};
      position: relative;
      overflow: hidden;
    }}
    .hero:after {{
      content: "";
      position: absolute;
      right: -40px;
      top: -40px;
      width: 180px;
      height: 180px;
      border-radius: 50%;
      background: {"radial-gradient(circle, rgba(251,191,36,0.20), transparent 68%)" if is_mythos else "radial-gradient(circle, rgba(200,156,39,0.16), transparent 68%)"};
      pointer-events: none;
    }}
    .hero h2 {{ margin-top: 0; }}
    .glance-item + .glance-item {{ margin-top: 14px; padding-top: 14px; border-top: 1px dashed rgba(31,41,55,0.12); }}
    .stack {{ display: grid; gap: 14px; }}
    .grid-two {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }}
    .card {{ padding: 20px; }}
    .area-card {{ background: {"linear-gradient(180deg, rgba(22,29,38,0.94), rgba(17,22,30,0.94))" if is_mythos else "linear-gradient(180deg, rgba(255,255,255,0.95), rgba(246,241,233,0.94))"}; }}
    .prose {{ padding: 22px; }}
    .key-pattern {{
      margin-top: 14px;
      padding: 12px 14px;
      border-radius: 16px;
      background: {"linear-gradient(135deg, rgba(13,56,61,0.92), rgba(20,72,76,0.92))" if is_mythos else "linear-gradient(135deg, var(--moss), #eef4e3)"};
      color: {"#d4fff8" if is_mythos else "#2f3a24"};
    }}
    .row {{ display: flex; justify-content: space-between; gap: 12px; align-items: center; }}
    .badge {{
      border-radius: 999px;
      background: {"rgba(255,255,255,0.06)" if is_mythos else "#f1eadb"};
      color: {"#d2dae3" if is_mythos else "#6a5b37"};
      padding: 4px 10px;
      font-size: 12px;
      white-space: nowrap;
    }}
    .section-intro {{ color: var(--muted); margin-bottom: 12px; }}
    .win {{ background: {"linear-gradient(180deg, #13261d, #173125)" if is_mythos else "linear-gradient(180deg, #edf8ea, #e6f5e2)"}; }}
    .friction {{ background: {"linear-gradient(180deg, #34191d, #281318)" if is_mythos else "linear-gradient(180deg, #fff1eb, #ffe9e2)"}; }}
    .feature {{ background: {"linear-gradient(180deg, #112333, #102a3c)" if is_mythos else "linear-gradient(180deg, #edf8ff, #e8f4ff)"}; }}
    .pattern {{ background: {"linear-gradient(180deg, #201930, #1a1527)" if is_mythos else "linear-gradient(180deg, #f7f5ff, #f2efff)"}; }}
    .horizon {{ background: {"linear-gradient(180deg, #20112d, #161a31)" if is_mythos else "linear-gradient(180deg, #f5efff, #f1e9ff)"}; }}
    pre {{
      margin: 10px 0 0;
      white-space: pre-wrap;
      word-break: break-word;
      background: {"rgba(255,255,255,0.04)" if is_mythos else "rgba(31,41,55,0.045)"};
      border: 1px solid rgba(31,41,55,0.08);
      padding: 13px 14px;
      border-radius: 14px;
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 12px;
    }}
    ul {{ margin: 10px 0 0 20px; padding: 0; }}
    .small-label {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 8px;
    }}
    .prompt-block {{ margin-top: 12px; }}
    .lede {{ color: {"#d6e1ec" if is_mythos else "#334155"}; font-weight: 600; }}
    .chart h3 {{ margin-bottom: 14px; }}
    .bar-row {{ display: flex; gap: 10px; align-items: center; margin-top: 10px; }}
    .bar-label {{ width: 120px; font-size: 12px; color: var(--muted); }}
    .bar-track {{ flex: 1; height: 8px; background: rgba(31,41,55,0.08); border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; border-radius: 999px; }}
    .bar-value {{ width: 34px; text-align: right; font-size: 12px; color: var(--muted); }}
    .fun-ending {{
      margin-top: 36px;
      padding: 26px 22px;
      text-align: center;
      border-radius: 28px;
      background: {"linear-gradient(135deg, #34230e 0%, #261a2d 55%, #132126 100%)" if is_mythos else "linear-gradient(135deg, #fff1c7 0%, #ffe3d2 55%, #fff8ef 100%)"};
      border: 1px solid {"rgba(251,191,36,0.32)" if is_mythos else "#efc97b"};
      box-shadow: {"0 18px 44px rgba(0,0,0,0.34)" if is_mythos else "0 16px 40px rgba(160,100,0,0.08)"};
    }}
    .fun-headline {{ font-size: 24px; font-weight: 800; color: {"#ffd166" if is_mythos else "#6e4b00"}; letter-spacing: -0.03em; }}
    .fun-detail {{ margin-top: 8px; color: {"#d9e7f4" if is_mythos else "#855f10"}; }}
    section[id] {{ scroll-margin-top: 26px; }}
    @media (max-width: 720px) {{
      .wrap {{ padding: 24px 14px 60px; }}
      h1 {{ font-size: 30px; }}
      .top-grid {{ grid-template-columns: 1fr; }}
      .nav-card {{ position: static; }}
      .row {{ align-items: flex-start; flex-direction: column; }}
      .bar-label {{ width: 92px; }}
    }}
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>{css}</style>
</head>
<body>
  <main class="wrap">
    <header>
      <div class="eyebrow">Insight Report</div>
      <h1>{esc(title)}</h1>
      <div class="subtitle">{esc(subtitle_line)}</div>
    </header>
    <section class="top-grid">
      <div>{''.join(section for section in sections[:2] if section)}</div>
      <aside class="nav-card">
        <h2>Report Map</h2>
        <div class="nav-links">{nav_html}</div>
      </aside>
    </section>
    {''.join(section for section in sections[2:] if section)}
  </main>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description="Render a polished Debrief HTML file from JSON.")
    parser.add_argument("input", help="Path to JSON input")
    parser.add_argument("-o", "--output", required=True, help="Path to HTML output")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    html_doc = render(data)
    output_path.write_text(html_doc, encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
