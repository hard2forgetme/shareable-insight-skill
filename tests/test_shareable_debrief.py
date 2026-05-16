#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEEKLY = ROOT / "debrief" / "scripts" / "build_weekly_debrief_report.py"
RENDERER = ROOT / "debrief" / "scripts" / "render_debrief_report.py"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def synthetic_session(session_id: str, cwd: str, prompt: str, close: str) -> list[dict]:
    return [
        {
            "timestamp": "2026-05-10T12:00:00Z",
            "type": "session_meta",
            "payload": {
                "id": session_id,
                "timestamp": "2026-05-10T12:00:00Z",
                "cwd": cwd,
            },
        },
        {
            "timestamp": "2026-05-10T12:00:01Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            },
        },
        {
            "timestamp": "2026-05-10T12:00:02Z",
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "shell.execute",
            },
        },
        {
            "timestamp": "2026-05-10T12:00:03Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": close}],
            },
        },
    ]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sessions_root = tmp_path / "sessions"
        output_json = tmp_path / "weekly.json"
        output_html = tmp_path / "weekly.html"
        day_dir = sessions_root / "2026" / "05" / "10"

        write_jsonl(
            day_dir / "session-one.jsonl",
            synthetic_session(
                "session-one",
                "/Users/private-person/dev/private-agent-project",
                "Please debug the agent automation and verify the repair for owner@example.test.",
                "Verified the automation repair and left a local proof receipt.",
            ),
        )
        write_jsonl(
            day_dir / "session-two.jsonl",
            synthetic_session(
                "session-two",
                "/Users/private-person/web/private-site",
                "Build the web dashboard and test it.",
                "Rendered the dashboard and ran the smoke test.",
            ),
        )

        subprocess.run(["python3", "-m", "py_compile", str(WEEKLY), str(RENDERER)], check=True)
        subprocess.run(
            [
                "python3",
                str(WEEKLY),
                "--sessions-root",
                str(sessions_root),
                "--start",
                date(2026, 5, 10).isoformat(),
                "--end",
                date(2026, 5, 10).isoformat(),
                "--sensitivity",
                "high",
                "--output-json",
                str(output_json),
                "--output-html",
                str(output_html),
            ],
            check=True,
        )

        assert output_json.stat().st_size > 0
        assert output_html.stat().st_size > 0
        report = json.loads(output_json.read_text(encoding="utf-8"))
        assert report["title"] == "Debrief Weekly Report"
        assert report["stats"][0]["value"] == "2"
        assert any(item["label"] == "Privacy" and item["value"] == "high" for item in report["stats"])

        combined = output_json.read_text(encoding="utf-8") + output_html.read_text(encoding="utf-8")
        forbidden = [
            "private-person",
            "Human Name + Agent Name",
            "/Users/private-person",
            "owner@example.test",
            "private-agent-project",
            "private-site",
        ]
        leaks = [item for item in forbidden if item in combined]
        assert not leaks, f"privacy leak(s): {leaks}"

    print("shareable debrief smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
