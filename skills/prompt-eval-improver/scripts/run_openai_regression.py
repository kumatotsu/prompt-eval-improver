from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import os
import re
import sys
import urllib.error
import urllib.request


ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = ROOT / "skills" / "prompt-eval-improver"
FIXTURE_DIR = SKILL_DIR / "fixtures"
REFERENCE_DIR = SKILL_DIR / "references"


@dataclass
class AssertionResult:
    fixture_id: str
    passed: bool
    missing_includes: list[str]
    forbidden_hits: list[str]


def parse_args() -> Any:
    parser = ArgumentParser(description="Run prompt-eval-improver regression fixtures against OpenAI Responses API")
    parser.add_argument("--model", default="gpt-5.4", help="OpenAI model name to call")
    parser.add_argument("--fixture", action="append", dest="fixtures", help="Fixture id to run. Repeatable.")
    parser.add_argument("--output-dir", help="Directory to store run artifacts")
    parser.add_argument("--dry-run", action="store_true", help="Write payloads without calling OpenAI")
    parser.add_argument("--base-url", default="https://api.openai.com/v1/responses", help="Responses API endpoint")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY", help="Environment variable name for the API key")
    parser.add_argument("--fail-on-assertion", action="store_true", help="Exit non-zero if any fixture assertion fails")
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(read_text(path))


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def select_fixture_paths(selected_ids: list[str] | None) -> list[Path]:
    fixture_paths = sorted(FIXTURE_DIR.glob("*.json"))
    if not selected_ids:
        return fixture_paths

    selected = {fixture_id.strip() for fixture_id in selected_ids if fixture_id.strip()}
    matched = [path for path in fixture_paths if path.stem in selected]
    missing = sorted(selected - {path.stem for path in matched})
    if missing:
        raise SystemExit(f"Unknown fixture ids: {', '.join(missing)}")
    return matched


def build_system_prompt() -> str:
    parts = [
        "You are executing the local Codex skill `prompt-eval-improver`.",
        "Follow the skill instructions and references below as the governing guidance for this run.",
        "",
        "=== SKILL.md ===",
        read_text(SKILL_DIR / "SKILL.md"),
        "",
        "=== references/openai-prompting-best-practices-2026-03.md ===",
        read_text(REFERENCE_DIR / "openai-prompting-best-practices-2026-03.md"),
        "",
        "=== references/output-templates.md ===",
        read_text(REFERENCE_DIR / "output-templates.md"),
    ]
    return "\n".join(parts)


def build_user_prompt(fixture: dict[str, Any]) -> str:
    lines = [
        "Use the `prompt-eval-improver` skill for this regression case.",
        "",
        "Regression fixture metadata:",
        f"- fixture_id: {fixture['id']}",
        f"- title: {fixture['title']}",
        f"- execution_environment: {fixture['environment']}",
        f"- review_mode: {fixture['review_mode']}",
        f"- task_type: {fixture['task_type']}",
        "",
        "Success criteria:",
    ]
    lines.extend(f"- {item}" for item in fixture["success_criteria"])
    lines.extend(
        [
            "",
            "User request:",
            fixture["user_request"],
            "",
            "Prompt to review:",
            "```text",
            fixture["input_prompt"],
            "```",
            "",
            "The answer should include these headings or sections when appropriate:",
        ]
    )
    lines.extend(f"- {item}" for item in fixture["must_include"])
    lines.extend(["", "The answer should avoid these failure patterns:"])
    lines.extend(f"- {item}" for item in fixture["must_not_include"])
    lines.extend(["", "Risks to catch:"])
    lines.extend(f"- {item}" for item in fixture["risks_to_catch"])
    return "\n".join(lines)


def build_payload(model: str, fixture: dict[str, Any]) -> dict[str, Any]:
    return {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": build_system_prompt()}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": build_user_prompt(fixture)}],
            },
        ],
    }


def extract_output_text(response_data: dict[str, Any]) -> str:
    if isinstance(response_data.get("output_text"), str) and response_data["output_text"].strip():
        return response_data["output_text"]

    output = response_data.get("output", [])
    chunks: list[str] = []
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            for content in item.get("content", []):
                if not isinstance(content, dict):
                    continue
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    chunks.append(text)
    return "\n".join(chunks).strip()


def call_openai(base_url: str, api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        base_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI API request failed: {exc}") from exc


def assert_response(fixture: dict[str, Any], output_text: str) -> AssertionResult:
    normalized_output = normalize_text(output_text)
    missing_includes = [
        item for item in fixture["must_include"] if normalize_text(item) not in normalized_output
    ]
    forbidden_hits = [
        item for item in fixture["must_not_include"] if normalize_text(item) in normalized_output
    ]
    return AssertionResult(
        fixture_id=str(fixture["id"]),
        passed=not missing_includes and not forbidden_hits,
        missing_includes=missing_includes,
        forbidden_hits=forbidden_hits,
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else ROOT / "runs" / "openai-regression" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    fixture_paths = select_fixture_paths(args.fixtures)
    api_key = os.environ.get(args.api_key_env)
    if not args.dry_run and not api_key:
        raise SystemExit(f"{args.api_key_env} is required unless --dry-run is used")

    run_summary: dict[str, Any] = {
        "model": args.model,
        "base_url": args.base_url,
        "dry_run": args.dry_run,
        "fixtures": [],
    }

    for fixture_path in fixture_paths:
        fixture = load_fixture(fixture_path)
        fixture_dir = output_dir / fixture_path.stem
        fixture_dir.mkdir(parents=True, exist_ok=True)

        payload = build_payload(args.model, fixture)
        write_json(fixture_dir / "request.json", payload)
        write_json(fixture_dir / "fixture.json", fixture)

        if args.dry_run:
            summary_entry = {
                "fixture_id": fixture["id"],
                "status": "dry-run",
                "artifact_dir": str(fixture_dir),
            }
            run_summary["fixtures"].append(summary_entry)
            continue

        response_data = call_openai(args.base_url, api_key, payload)
        write_json(fixture_dir / "response.json", response_data)

        output_text = extract_output_text(response_data)
        (fixture_dir / "output.md").write_text(output_text + "\n", encoding="utf-8")

        assertion = assert_response(fixture, output_text)
        write_json(
            fixture_dir / "assertion.json",
            {
                "fixture_id": assertion.fixture_id,
                "passed": assertion.passed,
                "missing_includes": assertion.missing_includes,
                "forbidden_hits": assertion.forbidden_hits,
            },
        )

        run_summary["fixtures"].append(
            {
                "fixture_id": fixture["id"],
                "status": "passed" if assertion.passed else "failed",
                "artifact_dir": str(fixture_dir),
                "missing_includes": assertion.missing_includes,
                "forbidden_hits": assertion.forbidden_hits,
            }
        )

    write_json(output_dir / "summary.json", run_summary)

    failures = [
        fixture for fixture in run_summary["fixtures"] if fixture["status"] == "failed"
    ]
    print(f"Run artifacts: {output_dir}")
    print(f"Fixtures processed: {len(run_summary['fixtures'])}")
    if args.dry_run:
        print("Dry-run completed without calling OpenAI")
        return 0
    if failures and args.fail_on_assertion:
        print(f"Assertion failures: {len(failures)}")
        return 1
    print(f"Assertion failures: {len(failures)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
