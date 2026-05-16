# Insight Report Schema

Create a JSON object with this shape. All fields are optional unless otherwise noted, but richer input produces a better report.

```json
{
  "title": "Debrief Report",
  "subtitle": "Short context line",
  "generated_at": "2026-04-08",
  "subject": "Human + Agent",
  "stats": [
    { "label": "Messages", "value": "42" },
    { "label": "Files", "value": "7" }
  ],
  "at_a_glance": [
    {
      "title": "What's working",
      "body": "2-3 sentences. **Bold** is supported.",
      "link_text": "See wins",
      "link_href": "#wins"
    }
  ],
  "work_areas": [
    {
      "name": "Workflow Design",
      "session_count": 3,
      "description": "What the work area was and how the agent helped."
    }
  ],
  "interaction_style": {
    "narrative": "2-3 paragraphs. **Bold** is supported.",
    "key_pattern": "One-sentence pattern summary"
  },
  "wins": {
    "intro": "Optional one-line intro",
    "items": [
      {
        "title": "Found the real source",
        "description": "Short explanation grounded in evidence."
      }
    ]
  },
  "friction": {
    "intro": "Optional one-line intro",
    "categories": [
      {
        "category": "Naming mismatch",
        "description": "What went wrong and why it mattered.",
        "examples": ["Expected /debrief, found /debriefs command instead"]
      }
    ]
  },
  "claude_md_additions": [
    {
      "addition": "Prefer checking local source dumps before browsing.",
      "why": "Why this repeat rule would help.",
      "prompt_scaffold": "Add under ## Workflow"
    }
  ],
  "features": [
    {
      "feature": "Custom Skills",
      "one_liner": "Reusable prompts and workflows.",
      "why_for_you": "Why it fits the observed pattern.",
      "example_code": "/debrief"
    }
  ],
  "patterns": [
    {
      "title": "Evidence-first deep dives",
      "suggestion": "Start from local source and only generalize after inspection.",
      "detail": "A few sentences on how to use this pattern.",
      "copyable_prompt": "Find the actual source implementation first, then mirror the behavior into the agent workflow."
    }
  ],
  "horizon": {
    "intro": "One-line future-looking intro",
    "opportunities": [
      {
        "title": "Report pipelines",
        "whats_possible": "What becomes possible next.",
        "how_to_try": "Concrete next step.",
        "copyable_prompt": "Generate a debrief report from the last 10 sessions and propose three reusable skills."
      }
    ]
  },
  "fun_ending": {
    "headline": "A short memorable close",
    "detail": "Optional context"
  },
  "charts": [
    {
      "title": "Top Themes",
      "bars": [
        { "label": "Source discovery", "value": 5, "color": "#2563eb" },
        { "label": "Skill design", "value": 4, "color": "#16a34a" }
      ]
    }
  ]
}
```

## Notes

- `**bold**` is supported in text fields that render long prose.
- Keep chart bar counts small and human-readable.
- Prefer concrete labels over abstract categories.
- If you do not have enough evidence for a section, omit it instead of inventing content.
