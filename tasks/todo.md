# TODO

## Plan

- [x] 現行スキルと参照ノートをレビューし、改善方針を特定する
- [x] GPT-5.4 時代の OpenAI 公式 guidance を確認する
- [x] `SKILL.md` と参照ファイルを GPT-5.4 前提に更新する
- [x] `agents/openai.yaml` を現行の挙動に合わせて更新する
- [x] ローカル検証スクリプトを追加して自己チェックできる状態にする
- [x] 検証を実行し、レビュー結果を記録する
- [x] 回帰テスト用 fixture を追加する
- [x] fixture の妥当性検証を self-check に組み込む
- [x] OpenAI Responses API を使う fixture 駆動の E2E runner を追加する

## Review

- `uv run python skills/prompt-eval-improver/scripts/validate_skill_docs.py` が成功
- `uv run python -m py_compile skills/prompt-eval-improver/scripts/validate_skill_docs.py` が成功
- `uv run python skills/prompt-eval-improver/scripts/validate_regression_suite.py` が成功
- `uv run python -m py_compile skills/prompt-eval-improver/scripts/validate_regression_suite.py` が成功
- `uv run python skills/prompt-eval-improver/scripts/run_openai_regression.py --dry-run --output-dir /tmp/prompt-eval-improver-dry-run` が成功
- `git diff --check` で空結果を確認
- 手動レビューで、旧 `GPT-5.2` 参照の除去と `GPT-5.4` 向け分岐の追加を確認
- ChatGPT / API / Codex を含む 4 件の fixture を追加
- `OPENAI_API_KEY` 未設定のため、live API 実行は未確認。dry-run で payload 生成フローを確認する
