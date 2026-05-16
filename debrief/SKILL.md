---
name: debrief
description: Generate a privacy-conscious usage, workflow, or weekly activity debrief report with polished local HTML output. Use when the user asks for a debrief, weekly recap, workflow retrospective, session analysis, wins/friction report, or next-step recommendations.
---

# Debrief

Use this skill when the user wants a polished reflective report, especially if they mention `/debrief`, `/debriefs`, `/weekly_debrief`, `/weekly_debriefs`, session analysis, workflow patterns, or a beautiful end report.

Debrief follows a four-phase report flow:
1. Collect session/source material.
2. Extract structured facets.
3. Generate concise narrative sections.
4. Render a polished HTML report.

## Privacy Defaults

This shareable version is designed not to expose machine-specific or personal details by default.

- Do not include full home-directory paths, usernames, private repo paths, tokens, emails, API keys, or account identifiers in generated reports.
- Use coarse labels like "Agent Tooling", "Operations", "Web/Product", or "General Build Work" unless the user explicitly asks for project names.
- Treat session snippets as potentially sensitive. Quote sparingly and paraphrase when enough context exists.
- Keep generated reports local unless the user explicitly asks to share or publish them.

## What to Analyze

Build the report from the best available source material:
- The current conversation and actions taken in this turn.
- Files, diffs, logs, notes, or transcripts the user points to.
- Session artifacts in local folders if the user explicitly asks for historical analysis.
- Weekly session artifacts when the user asks for an overall weekly report.

If no historical corpus is available, generate the report from the current task and say that clearly in the subtitle or intro.

## Focused Report Workflow

1. Gather evidence.
2. Build structured report data matching `references/report_schema.md`.
3. Render the HTML report from the installed skill directory:

```bash
python3 scripts/render_debrief_report.py /tmp/debrief-report.json -o /tmp/debrief-report.html
```

4. Confirm the HTML file exists and is non-empty.
5. Respond with a short summary, the report path, and the highest-value recommendation.

## Weekly Report Mode

For an overall weekly report, run from the installed skill directory:

```bash
python3 scripts/build_weekly_debrief_report.py
```

The weekly builder reads local session JSONL files, creates `/tmp/debrief-weekly-report.json`, and renders `/tmp/debrief-weekly-report.html`.

For explicit ranges:

```bash
python3 scripts/build_weekly_debrief_report.py --start YYYY-MM-DD --end YYYY-MM-DD
```

For non-default session roots:

```bash
python3 scripts/build_weekly_debrief_report.py --sessions-root /path/to/sessions
```

For audience-specific privacy:

```bash
python3 scripts/build_weekly_debrief_report.py --sensitivity high
```

Sensitivity levels:
- `low`: redacts emails and common secret-looking assignments, keeps sanitized workspace paths.
- `medium`: also redacts home-directory paths.
- `high`: also suppresses path-like spans and uses generic workspace labels. This is the default.

Treat the output as a grounded scaffold. It is useful for "what did we do this week?" and "where should we deepen next?", but important claims should be deepened by reading the underlying session artifacts.

## Section Design

Prefer these sections:
- At a Glance
- What You Work On
- How You Use the Agent
- Impressive Things You Did
- Where Things Go Wrong
- Existing Features to Try
- New Usage Patterns
- On the Horizon
- A closing memorable note

Optional:
- Charts or bar groups
- Suggested instruction additions
- Copyable prompts or commands

## Tone

Use second person where natural.
Be specific and grounded.
Do not be gushy.
Do not invent evidence.
If something is inferred rather than directly observed, state that.

## Report Quality Bar

The report should feel polished, not like raw notes:
- Strong title and subtitle
- Compact top-line summary
- Card-based sections
- Clear contrast between wins, friction, and recommendations
- Copyable prompts/commands when useful

## Files

- Read `references/report_schema.md` before writing report JSON by hand.
- Use `scripts/render_debrief_report.py` to generate focused HTML reports.
- Use `scripts/build_weekly_debrief_report.py` for `/weekly_debrief` and weekly-overview requests.
