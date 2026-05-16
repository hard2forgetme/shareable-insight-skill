# Debrief Skill

Debrief is a privacy-conscious agent reporting skill for creating local HTML/JSON retrospectives from current work, explicit report JSON, or JSONL session logs.

It intentionally avoids Claude Code's built-in `/insights` name. Use Debrief when you want a portable, shareable, redaction-aware report artifact rather than a product-specific usage analysis.

## Commands

- `/debrief`
- `/debriefs`
- `/weekly_debrief`
- `/weekly_debriefs`

## Why Use This Instead Of Built-In Insights?

- **Portable session roots:** works with exported or custom JSONL session directories, not only one tool's default history.
- **Weekly reports:** aggregates sessions by date range for team/status recaps.
- **Privacy controls:** `--sensitivity low|medium|high`, with `high` as the default.
- **Shareable artifacts:** emits local HTML and JSON designed for review before sharing.
- **Tested redaction path:** synthetic sessions verify path/email redaction and report rendering.

## Privacy Posture

- No user home-directory paths are embedded in the package.
- No private project names from the source machine are embedded.
- Weekly reports redact emails and common secret-looking assignments at every sensitivity level.
- `medium` redacts home paths.
- `high` also suppresses path-like spans and uses generic workspace labels.
- Generated HTML stays local unless the user explicitly chooses to share it.

Still treat session logs as sensitive. If you plan to publish a generated report, review it first.

## Install

Copy the `debrief/` folder into your agent skill directory.

For Codex-style command cards, copy the files in `commands/` into your command directory.

Example layout:

```text
skills/
  debrief/
    SKILL.md
    references/report_schema.md
    scripts/render_debrief_report.py
    scripts/build_weekly_debrief_report.py
commands/
  debrief.md
  debriefs.md
  weekly_debrief.md
  weekly_debriefs.md
```

## Focused Report

Create JSON using `debrief/references/report_schema.md`, then run from the installed skill directory:

```bash
python3 scripts/render_debrief_report.py /tmp/debrief-report.json -o /tmp/debrief-report.html
```

## Weekly Report

The weekly builder expects session logs arranged as:

```text
sessions-root/
  YYYY/
    MM/
      DD/
        session.jsonl
```

Run from the installed skill directory:

```bash
python3 scripts/build_weekly_debrief_report.py --sessions-root /path/to/sessions
```

For explicit ranges and stricter sharing:

```bash
python3 scripts/build_weekly_debrief_report.py --sessions-root /path/to/sessions --start 2026-05-10 --end 2026-05-16 --sensitivity high
```

Outputs default to:

```text
/tmp/debrief-weekly-report.json
/tmp/debrief-weekly-report.html
```

## Sensitivity Levels

- `low`: redacts emails and common secret-looking assignments, keeps sanitized workspace paths.
- `medium`: also redacts home-directory paths.
- `high`: also suppresses path-like spans and uses generic workspace labels.

## Test

From this package root:

```bash
python3 tests/test_shareable_debrief.py
```

The test creates synthetic session logs, runs the weekly builder, renders HTML, and checks that personal source-machine strings are not present.
