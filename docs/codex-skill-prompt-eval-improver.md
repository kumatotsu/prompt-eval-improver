# codex-skill-prompt-eval-improver

更新日: 2026-03-07

## 目的

- 既存の「プロンプト評価・改善」用途の長大プロンプトを、再利用可能な Codex Skill に分離する
- 旧ルールの良い点（評価観点・差分説明・停止条件）を残しつつ、GPT-5.4 時代の OpenAI 公式ガイドに合わせて過剰拘束を減らす

## 重要な前提

- 対象は OpenAI 系（ChatGPT / OpenAI API / Codex）の「プロンプトの分析・評価・改善」であり、実装コード生成そのものではない
- モデル/バージョン依存の最適化は日付依存情報として扱う
- 「最新」指定時はWebで一次情報（公式Docs/Cookbook）を確認する
- `GPT-5.4` 向けの現行 guidance を参照し、ChatGPT / API / Codex を分けて扱う

## 設計判断

1. 新規 Skill 名を `prompt-eval-improver` とした

- 役割（評価 + 改善）が明確
- 既存 `skills/` 配下の命名規則（ハイフン区切り）に合わせた

2. SKILL 本体と参照ノートを分離した

- `SKILL.md` は運用フロー中心にし、肥大化を避ける
- 最新ベストプラクティスの要点は `references/` に切り出した
- 月次で更新しやすいように、日付付き snapshot を採用した

3. 固定フォーマット強制と固定採点を弱めた

- 旧プロンプトの `1〜11` 固定順序は再利用性を下げるため採用しない
- 代わりに「簡易版 / 詳細版」テンプレートで運用負荷を調整できるようにした
- `10項目×10点` は詳細レビュー時のみ既定とし、通常は軽量レビューを優先する

4. 実行環境別の分岐を追加した

- ChatGPT / OpenAI API / Codex では、改善案の望ましい形が異なる
- API では prompt object と eval、Codex では tool policy と verification loop を重視する

## 検証メモ

- `skills/prompt-eval-improver/scripts/validate_skill_docs.py` を追加し、必須ファイルと内容整合を確認できるようにした
- YAML frontmatter は `name` / `description` のみで作成

## 追加対応（2026-03-07）

- `GPT-5.4` の公開情報と現行 prompt guidance を反映
- 実行環境別の分岐を `SKILL.md` とテンプレートへ反映
- `10項目×10点` を詳細レビュー時のモードへ移動
