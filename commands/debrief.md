# /debrief

Generate a polished, privacy-conscious Debrief report from the current conversation, a named session, or a project/workspace.

## Arguments

- `subject`: optional topic, session path, repo path, or report focus

## Workflow

1. Use the `debrief` skill.
2. Treat all text after `/debrief` as the report subject. If no text follows, use the current conversation and the work just performed.
3. Build `/tmp/debrief-report.json` using the schema in `debrief/references/report_schema.md`.
4. Render the report from the installed skill directory:

```bash
python3 scripts/render_debrief_report.py /tmp/debrief-report.json -o /tmp/debrief-report.html
```

5. Verify the HTML exists and is non-empty, then respond with the report path, a short summary, and the highest-value recommendation.

## Guardrails

- Ground claims in observed conversation, files, diffs, logs, or collected evidence.
- Do not invent historical patterns when the source corpus is only the current turn.
- Do not include usernames, home-directory paths, private repo paths, tokens, emails, or account identifiers.
- Prefer a beautiful HTML artifact over raw notes.
- If evidence is thin, say that in the report subtitle or intro.
