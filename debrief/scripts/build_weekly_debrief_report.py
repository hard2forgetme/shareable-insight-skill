#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_SESSIONS_ROOT = Path(os.environ.get("AGENT_SESSIONS_ROOT", Path.home() / ".codex" / "sessions"))
DEFAULT_RENDERER = SCRIPT_DIR / "render_debrief_report.py"
SENSITIVITY_CHOICES = ("low", "medium", "high")

PROJECT_HINTS = {
    "Agent Tooling": ("agent", "runtime", "skill", "command", "plugin", "automation", "memory"),
    "Operations": ("launch", "daemon", "service", "health", "doctor", "repair", "backup"),
    "Data/Research": ("research", "dataset", "analysis", "report", "extract", "summarize"),
    "Creative Production": ("image", "video", "film", "storyboard", "asset", "scene"),
    "Web/Product": ("website", "web", "frontend", "react", "vite", "next"),
    "macOS Tools": ("macos", "swift", ".app", "launchagent", "quick action"),
}

ACTION_WORDS = (
    "build",
    "fix",
    "debug",
    "restore",
    "verify",
    "test",
    "ship",
    "audit",
    "analyze",
    "implement",
    "update",
    "recover",
)


def parse_day(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def day_dirs(root: Path, start: date, end: date) -> list[Path]:
    dirs: list[Path] = []
    current = start
    while current <= end:
        path = root / f"{current:%Y}" / f"{current:%m}" / f"{current:%d}"
        if path.exists():
            dirs.append(path)
        current += timedelta(days=1)
    return dirs


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return records


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("input_text") or item.get("output_text")
        if isinstance(text, str):
            parts.append(text)
    return "\n".join(parts)


def clean_snippet(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"<[^>]{0,80}>", "", text)
    return text[:limit].rstrip()


def safe_workspace_label(path_value: str, sensitivity: str) -> str:
    if not path_value:
        return "an unknown workspace"
    if sensitivity == "high":
        return "workspace"
    path = Path(path_value).expanduser()
    name = path.name or "workspace"
    if sensitivity == "low":
        return str(path).replace(str(Path.home()), "~")
    parent = path.parent.name if path.parent and path.parent.name else ""
    if parent and parent not in {".", "/", str(Path.home())}:
        return f"{parent}/{name}"
    return name


def redact_sensitive_text(text: str, sensitivity: str) -> str:
    if not text:
        return ""
    redacted = text
    if sensitivity in {"medium", "high"}:
        home = str(Path.home())
        redacted = redacted.replace(home, "~")
        redacted = re.sub(r"/Users/[^/\s]+", "~", redacted)
    if sensitivity == "high":
        redacted = re.sub(r"(?<!\w)/(?:[\w .@+-]+/){1,}[\w .@+-]+", "[path]", redacted)
    redacted = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]", redacted)
    redacted = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]+", r"\1=[redacted]", redacted)
    return redacted


def classify(text: str) -> str:
    lowered = text.lower()
    for label, hints in PROJECT_HINTS.items():
        if any(hint in lowered for hint in hints):
            return label
    return "General Build Work"


def action_signal(text: str) -> str | None:
    lowered = text.lower()
    for word in ACTION_WORDS:
        if re.search(rf"\b{re.escape(word)}\w*\b", lowered):
            return word
    return None


def summarize_session(path: Path, sensitivity: str) -> dict[str, Any] | None:
    records = load_jsonl(path)
    if not records:
        return None

    meta: dict[str, Any] = {}
    user_texts: list[str] = []
    assistant_texts: list[str] = []
    tool_names: Counter[str] = Counter()

    for record in records:
        payload = record.get("payload") or {}
        record_type = record.get("type")
        if record_type == "session_meta" and isinstance(payload, dict):
            meta.update(payload)
            continue
        if record_type != "response_item":
            continue
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")
        if payload_type == "message":
            role = payload.get("role")
            text = text_from_content(payload.get("content"))
            if role == "user" and text:
                user_texts.append(text)
            elif role == "assistant" and text:
                assistant_texts.append(text)
        elif payload_type == "function_call":
            name = payload.get("name")
            if isinstance(name, str):
                tool_names[name] += 1

    first_user = next((clean_snippet(redact_sensitive_text(text, sensitivity)) for text in user_texts if clean_snippet(text)), "")
    assistant_close = next((clean_snippet(redact_sensitive_text(text, sensitivity)) for text in reversed(assistant_texts) if clean_snippet(text)), "")
    combined = " ".join([str(meta.get("cwd", "")), first_user, assistant_close])
    return {
        "path": str(path),
        "id": meta.get("id") or path.stem,
        "timestamp": meta.get("timestamp") or records[0].get("timestamp"),
        "cwd": meta.get("cwd", ""),
        "first_user": first_user,
        "assistant_close": assistant_close,
        "category": classify(combined),
        "action": action_signal(combined),
        "tools": dict(tool_names.most_common(8)),
        "message_count": len(user_texts) + len(assistant_texts),
    }


def collect_sessions(root: Path, start: date, end: date, max_sessions: int, sensitivity: str) -> list[dict[str, Any]]:
    files: list[Path] = []
    for directory in day_dirs(root, start, end):
        files.extend(sorted(directory.glob("*.jsonl")))
    files = sorted(files, key=lambda p: p.stat().st_mtime if p.exists() else 0)
    if max_sessions > 0:
        files = files[-max_sessions:]
    sessions = [summary for path in files if (summary := summarize_session(path, sensitivity))]
    return sessions


def build_report(sessions: list[dict[str, Any]], start: date, end: date, sensitivity: str) -> dict[str, Any]:
    categories = Counter(session["category"] for session in sessions)
    actions = Counter(session["action"] for session in sessions if session.get("action"))
    tool_counts: Counter[str] = Counter()
    cwd_counts: Counter[str] = Counter()
    for session in sessions:
        tool_counts.update(session.get("tools", {}))
        cwd = session.get("cwd")
        if cwd:
            cwd_counts[str(cwd)] += 1

    work_areas = [
        {
            "name": name,
            "session_count": count,
            "description": f"Detected from session paths, prompts, and closing summaries across {count} session(s).",
        }
        for name, count in categories.most_common(8)
    ]

    notable = [
        session
        for session in sessions
        if session.get("first_user") or session.get("assistant_close")
    ][-8:]

    wins = []
    for session in notable[-5:]:
        title = session.get("first_user") or session.get("assistant_close") or "Session activity"
        wins.append(
            {
                "title": clean_snippet(title, 96),
                "description": clean_snippet(
                    session.get("assistant_close") or f"Worked in {safe_workspace_label(session.get('cwd', ''), sensitivity)}.",
                    260,
                ),
            }
        )

    friction_categories = []
    if not sessions:
        friction_categories.append(
            {
                "category": "No session corpus found",
                "description": "The weekly collector did not find Codex JSONL sessions in the selected date range.",
                "examples": [f"{start.isoformat()} through {end.isoformat()}"],
            }
        )
    if len(cwd_counts) > 12:
        friction_categories.append(
            {
                "category": "Wide workspace spread",
                "description": "Work spanned many directories, so future reports should cluster by project before drawing conclusions.",
                "examples": [safe_workspace_label(path, sensitivity) for path, _count in cwd_counts.most_common(3)],
            }
        )
    if not tool_counts:
        friction_categories.append(
            {
                "category": "Low tool signal",
                "description": "The parsed sessions did not expose many tool-call records, so the report leans more on prompts and summaries.",
                "examples": ["Use explicit verification commands for richer weekly proof."],
            }
        )

    charts = []
    if categories:
        charts.append(
            {
                "title": "Work Areas",
                "bars": [
                    {"label": label, "value": value, "color": "#2563eb"}
                    for label, value in categories.most_common(8)
                ],
            }
        )
    if actions:
        charts.append(
            {
                "title": "Action Signals",
                "bars": [
                    {"label": label, "value": value, "color": "#16a34a"}
                    for label, value in actions.most_common(8)
                ],
            }
        )

    top_tools = ", ".join(name for name, _count in tool_counts.most_common(5)) or "limited tool-call signal"
    date_label = f"{start.isoformat()} to {end.isoformat()}"
    return {
        "title": "Debrief Weekly Report",
        "subtitle": f"Grounded from local session artifacts for {date_label}",
        "generated_at": datetime.now(timezone.utc).date().isoformat(),
        "subject": "Human + Agent",
        "stats": [
            {"label": "Sessions", "value": str(len(sessions))},
            {"label": "Work areas", "value": str(len(categories))},
            {"label": "Top tools", "value": str(len(tool_counts))},
            {"label": "Privacy", "value": sensitivity},
        ],
        "at_a_glance": [
            {
                "title": "What this report is",
                "body": f"A deterministic weekly pass over local JSONL session artifacts using **{sensitivity}** privacy sensitivity. It is grounded, but intentionally conservative: ambiguous sessions are labeled broadly rather than over-interpreted.",
            },
            {
                "title": "Dominant pattern",
                "body": f"Most visible activity clustered around **{categories.most_common(1)[0][0] if categories else 'no detected category'}**. Tool signal centered on {top_tools}.",
            },
        ],
        "work_areas": work_areas,
        "interaction_style": {
            "narrative": (
                "This week shows a strong bias toward operational closure: find the real local surface, restore or repair it, then verify with a concrete artifact. "
                "The session corpus also shows frequent movement between project work and host tooling, which makes provenance and durable commands especially valuable.\n\n"
                "Because this report is generated from session artifacts rather than full semantic rereading by a model, treat it as the grounded weekly scaffold. "
                "The agent can then deepen any section by rereading the named sessions."
            ),
            "key_pattern": "Ground locally, make the workflow durable, then leave proof behind.",
        },
        "wins": {
            "intro": "Recent sessions with concrete prompts or closing summaries:",
            "items": wins,
        },
        "friction": {
            "intro": "Signals that can make weekly synthesis fuzzier:",
            "categories": friction_categories,
        },
        "features": [
            {
                "feature": "/weekly_debrief",
                "one_liner": "Generate this report from the last seven days of local session artifacts.",
                "why_for_you": "It turns scattered session history into a browsable weekly artifact without needing to manually collect transcripts.",
                "example_code": "/weekly_debrief",
            },
            {
                "feature": "/debrief",
                "one_liner": "Generate a focused polished report from a session, project, or current conversation.",
                "why_for_you": "Use it when one thread deserves a deeper postmortem than the weekly overview.",
                "example_code": "/debrief this session",
            },
        ],
        "patterns": [
            {
                "title": "Weekly review as an operating ritual",
                "suggestion": "Use the weekly report as the top-level map, then open only the sessions that need deeper synthesis.",
                "detail": "The report highlights clusters, recent prompts, likely wins, friction, and proof gaps. That gives the next thread a grounded starting point without loading the entire week into context.",
                "copyable_prompt": "/weekly_debrief last 7 days, then deepen the top three work areas into reusable next actions",
            }
        ],
        "horizon": {
            "intro": "Useful upgrades now that weekly reporting is first-class:",
            "opportunities": [
                {
                    "title": "Scheduled weekly digest",
                    "whats_possible": "A recurring automation can generate the HTML report every Friday or Sunday and drop it into an inbox item.",
                    "how_to_try": "Ask your agent to create a weekly heartbeat or cron automation for /weekly_debrief.",
                    "copyable_prompt": "Create a weekly automation that runs /weekly_debrief every Friday afternoon and summarizes the report path.",
                }
            ],
        },
        "charts": charts,
        "fun_ending": {
            "headline": "The week has a map now.",
            "detail": "Not a perfect oracle, but a real, repeatable proof surface.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a polished weekly Debrief report from local session JSONL files.")
    parser.add_argument("--sessions-root", default=str(DEFAULT_SESSIONS_ROOT))
    parser.add_argument("--start", help="Start date, YYYY-MM-DD. Defaults to end minus days plus one.")
    parser.add_argument("--end", default=datetime.now().date().isoformat(), help="End date, YYYY-MM-DD. Defaults to today.")
    parser.add_argument("--days", type=int, default=7, help="Number of days to include when --start is omitted.")
    parser.add_argument("--max-sessions", type=int, default=0, help="Limit to most recent N sessions. 0 means no limit.")
    parser.add_argument("--sensitivity", choices=SENSITIVITY_CHOICES, default="high", help="Redaction strength: low keeps sanitized paths, medium redacts home paths, high also suppresses path-like spans and workspace labels.")
    parser.add_argument("--output-json", default="/tmp/debrief-weekly-report.json")
    parser.add_argument("--output-html", default="/tmp/debrief-weekly-report.html")
    parser.add_argument("--no-render", action="store_true", help="Only write the report JSON.")
    args = parser.parse_args()

    end = parse_day(args.end)
    start = parse_day(args.start) if args.start else end - timedelta(days=max(args.days, 1) - 1)
    root = Path(args.sessions_root).expanduser().resolve()
    sessions = collect_sessions(root, start, end, args.max_sessions, args.sensitivity)
    report = build_report(sessions, start, end, args.sensitivity)

    json_path = Path(args.output_json).expanduser().resolve()
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    if args.no_render:
        print(str(json_path))
        return 0

    html_path = Path(args.output_html).expanduser().resolve()
    html_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["python3", str(DEFAULT_RENDERER), str(json_path), "-o", str(html_path)],
        check=True,
    )
    print(str(html_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
