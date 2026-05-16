# /weekly_debrief

Generate a polished weekly Debrief report from local session artifacts.

## Arguments

- Optional date range such as `last 7 days`, `2026-05-10 to 2026-05-16`, or `this week`.

## Workflow

1. Use the `debrief` skill.
2. Run the weekly report builder from the installed skill directory. Defaults to the last seven calendar days ending today:

```bash
python3 scripts/build_weekly_debrief_report.py
```

3. For an explicit date range, pass `--start` and `--end`:

```bash
python3 scripts/build_weekly_debrief_report.py --start YYYY-MM-DD --end YYYY-MM-DD
```

4. For exported or non-default session logs, pass `--sessions-root`:

```bash
python3 scripts/build_weekly_debrief_report.py --sessions-root /path/to/sessions
```

5. For audience-specific privacy, pass `--sensitivity low|medium|high`. Default is `high`:

```bash
python3 scripts/build_weekly_debrief_report.py --sensitivity high
```

6. Verify both outputs exist and are non-empty:

```text
/tmp/debrief-weekly-report.json
/tmp/debrief-weekly-report.html
```

7. Respond with the HTML path, session count, dominant work areas, privacy sensitivity, and any confidence caveats.

## Guardrails

- Treat this as a grounded weekly scaffold, not omniscient memory.
- Do not claim semantic certainty from sparse session snippets.
- Do not include usernames, home-directory paths, private repo paths, tokens, emails, or account identifiers.
- If a section matters, deepen it by reading the named sessions before making decisions.
- Keep the report local unless the user explicitly asks to publish or share it.
