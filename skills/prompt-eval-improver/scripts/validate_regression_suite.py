from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = ROOT / "skills" / "prompt-eval-improver" / "fixtures"

REQUIRED_FIELDS = {
    "id",
    "title",
    "environment",
    "review_mode",
    "task_type",
    "success_criteria",
    "user_request",
    "input_prompt",
    "must_include",
    "must_not_include",
    "risks_to_catch",
}
EXPECTED_ENVIRONMENTS = {"ChatGPT", "OpenAI API", "Codex"}
EXPECTED_REVIEW_MODES = {"light", "detailed"}


def error(message: str, errors: list[str]) -> None:
    errors.append(message)


def load_fixture(path: Path, errors: list[str]) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(f"{path.name}: invalid JSON ({exc})", errors)
        return None

    missing = REQUIRED_FIELDS - set(data)
    if missing:
        error(f"{path.name}: missing fields {sorted(missing)}", errors)
        return None

    for field in ("success_criteria", "must_include", "must_not_include", "risks_to_catch"):
        value = data.get(field)
        if not isinstance(value, list) or not value or not all(isinstance(item, str) and item.strip() for item in value):
            error(f"{path.name}: field '{field}' must be a non-empty list of non-empty strings", errors)

    for field in ("id", "title", "environment", "review_mode", "task_type", "user_request", "input_prompt"):
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            error(f"{path.name}: field '{field}' must be a non-empty string", errors)

    return data


def main() -> int:
    errors: list[str] = []
    if not FIXTURE_DIR.exists():
        error(f"missing fixture directory: {FIXTURE_DIR}", errors)
    fixture_paths = sorted(FIXTURE_DIR.glob("*.json"))
    if len(fixture_paths) < 4:
        error("expected at least 4 regression fixture files", errors)

    fixtures: list[dict[str, object]] = []
    ids: set[str] = set()
    environments = Counter()
    review_modes = Counter()

    for path in fixture_paths:
        fixture = load_fixture(path, errors)
        if fixture is None:
            continue
        fixture_id = fixture["id"]
        if fixture_id in ids:
            error(f"{path.name}: duplicate fixture id '{fixture_id}'", errors)
        ids.add(fixture_id)
        fixtures.append(fixture)
        environments[str(fixture["environment"])] += 1
        review_modes[str(fixture["review_mode"])] += 1

    for fixture in fixtures:
        path_name = f"{fixture['id']}.json"
        environment = str(fixture["environment"])
        review_mode = str(fixture["review_mode"])

        if environment not in EXPECTED_ENVIRONMENTS:
            error(f"{path_name}: unexpected environment '{environment}'", errors)
        if review_mode not in EXPECTED_REVIEW_MODES:
            error(f"{path_name}: unexpected review_mode '{review_mode}'", errors)

        if environment == "OpenAI API" and "API向け prompt object 案" not in fixture["must_include"] and review_mode == "detailed":
            error(f"{path_name}: detailed API fixture should require a prompt object section", errors)
        if environment == "Codex" and not any("tool" in item.lower() or "verification" in item.lower() for item in fixture["risks_to_catch"]):
            error(f"{path_name}: Codex fixture should cover tool or verification risks", errors)

    if set(environments) != EXPECTED_ENVIRONMENTS:
        error(f"fixture coverage missing environments: {sorted(EXPECTED_ENVIRONMENTS - set(environments))}", errors)
    if set(review_modes) != EXPECTED_REVIEW_MODES:
        error(f"fixture coverage missing review modes: {sorted(EXPECTED_REVIEW_MODES - set(review_modes))}", errors)

    if errors:
        for message in errors:
            print(f"ERROR: {message}")
        return 1

    print("OK: regression fixture suite passed validation")
    print(f"fixtures: {len(fixtures)}")
    print(f"environments: {dict(environments)}")
    print(f"review_modes: {dict(review_modes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
