from __future__ import annotations

from pathlib import Path
import re
import sys
import subprocess


ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = ROOT / "skills" / "prompt-eval-improver"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []

    skill_path = SKILL_DIR / "SKILL.md"
    ref_path = SKILL_DIR / "references" / "openai-prompting-best-practices-2026-03.md"
    tmpl_path = SKILL_DIR / "references" / "output-templates.md"
    agent_path = SKILL_DIR / "agents" / "openai.yaml"
    fixture_dir = SKILL_DIR / "fixtures"
    regression_validator_path = SKILL_DIR / "scripts" / "validate_regression_suite.py"
    e2e_runner_path = SKILL_DIR / "scripts" / "run_openai_regression.py"

    for path in (skill_path, ref_path, tmpl_path, agent_path, fixture_dir, regression_validator_path, e2e_runner_path):
        require(path.exists(), f"missing required file: {path}", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    skill = read_text(skill_path)
    ref = read_text(ref_path)
    tmpl = read_text(tmpl_path)
    agent = read_text(agent_path)

    frontmatter = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
    require(frontmatter is not None, "SKILL.md is missing YAML frontmatter", errors)
    require("name: prompt-eval-improver" in skill, "SKILL.md must declare the skill name", errors)
    require("description:" in skill, "SKILL.md must declare a description", errors)

    for needle in (
        "GPT-5.4",
        "ChatGPT",
        "OpenAI API",
        "Codex / agentic",
        "Prompt guidance / Prompting overview",
        "references/openai-prompting-best-practices-2026-03.md",
    ):
        require(needle in skill, f"SKILL.md missing expected guidance marker: {needle}", errors)

    require("GPT-5.2" not in skill, "SKILL.md still references GPT-5.2", errors)

    for needle in (
        "https://openai.com/index/introducing-gpt-5-4/",
        "https://developers.openai.com/api/docs/models/gpt-5.4",
        "https://developers.openai.com/api/docs/guides/prompt-guidance",
        "https://developers.openai.com/api/docs/guides/prompting",
        "https://developers.openai.com/api/docs/guides/prompt-optimizer",
        "https://developers.openai.com/api/docs/guides/tools",
    ):
        require(needle in ref, f"reference note missing source: {needle}", errors)

    for needle in (
        "実行環境メモ",
        "API向け prompt object 案",
        "最小 eval 案",
    ):
        require(needle in tmpl, f"output templates missing section: {needle}", errors)

    require(len(list(fixture_dir.glob("*.json"))) >= 4, "expected at least 4 regression fixtures", errors)

    require("10項目×10点で評価" not in agent, "openai.yaml default prompt is still hard-coded to always score", errors)
    for needle in (
        'display_name: "OpenAI Prompt Reviewer"',
        "GPT-5.4",
        "必要なら詳細採点",
    ):
        require(needle in agent, f"openai.yaml missing expected content: {needle}", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    result = subprocess.run(
        [sys.executable, str(regression_validator_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        return result.returncode

    print("OK: prompt-eval-improver skill files passed validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
