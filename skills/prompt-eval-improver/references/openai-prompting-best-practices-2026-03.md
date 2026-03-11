# OpenAI Prompting Best Practices (Snapshot: 2026-03-07)

このメモは `prompt-eval-improver` Skill 用の参照ノートです。OpenAI 系（ChatGPT / OpenAI API / Codex）向けを主対象にしています。日付依存のため、ユーザーが「最新」を求める場合は再確認してください。

## 使い方

- OpenAI 系モデル向けにプロンプト改善する場合に読む
- `GPT-5.4` 固有の guidance と、モデル横断の一般原則を分けて適用する
- ルールをそのまま転写せず、対象タスクと実行環境に合わせて最小限を採用する

## 参照元（一次情報）

- OpenAI: Introducing GPT-5.4
  - https://openai.com/index/introducing-gpt-5-4/
- OpenAI Docs: GPT-5.4 model page
  - https://developers.openai.com/api/docs/models/gpt-5.4
- OpenAI Docs: Latest model guide
  - https://developers.openai.com/api/docs/guides/latest-model
- OpenAI Docs: Prompt guidance for GPT-5.4
  - https://developers.openai.com/api/docs/guides/prompt-guidance
- OpenAI Docs: Prompting overview
  - https://developers.openai.com/api/docs/guides/prompting
- OpenAI Docs: Prompt optimizer
  - https://developers.openai.com/api/docs/guides/prompt-optimizer
- OpenAI Docs: Using tools
  - https://developers.openai.com/api/docs/guides/tools
- OpenAI Docs: Tool search
  - https://developers.openai.com/api/docs/guides/tools-tool-search
- OpenAI Docs: Computer use
  - https://developers.openai.com/api/docs/guides/tools-computer-use
- OpenAI: GPT-5 for Coding cheatsheet
  - https://cdn.openai.com/API/docs/gpt-5-for-coding-cheatsheet.pdf

## 要点（一般原則）

1. 先に契約を明確にする

- 目的、成功条件、出力形式、完了条件を先に固定する
- `output contract` と `completeness contract` を曖昧にしない
- 形式制約が強いときは、短い schema や例を使う

2. プロンプト本文と実行時設定を分ける

- `reasoning_effort`、ツール設定、phase などは本文から分離する
- モデル更新で変わりやすい設定を本文へ埋め込みすぎない
- 安定運用が必要ならスナップショット名も候補に入れる

3. 少数の高品質な指示へ絞る

- あいまい、競合、過剰に強い命令を混在させない
- 「Be thorough」のような曖昧な強調だけに頼らない
- few-shot は短い YAML や箇条書きで最小限にする

4. 再利用しやすい形へ寄せる

- API 向けでは prompt object、variables、versioning を優先する
- linked evals や grader を作りやすいように、期待挙動を分解しておく
- 長い共通 prefix は安定させて prompt caching と相性を良くする

## 要点（GPT-5.4 / agentic 向け）

1. ツール利用方針を明文化する

- 正確性、完全性、根拠づけに実質的に効くならツールを使う
- 逆に不要なツール呼び出しを避ける条件も書く
- 大きいツール集合では `tool_search` を優先する

2. verification loop と stop condition を定義する

- 検証が終わる前に確定回答しない
- 依存がある手順は逐次、独立な探索だけ selective parallelism を使う
- 「何を確認したら止めてよいか」を明示する

3. 長時間フローは phase を分ける

- `commentary` と `final_answer` を混ぜない
- 途中経過は簡潔に、最終出力は利用者向けに整える

4. computer use は前提条件込みで設計する

- 画面の状態確認、再試行条件、失敗時の戻り方を含める
- スクリーンショット前提の精度要件がある場合は detail 設定も意識する

## 実行環境別の示唆

- ChatGPT:
  - 会話内でそのまま使える短めの完成形を優先する
  - API 固有の設定名や tool schema は本文へ持ち込みすぎない
- OpenAI API:
  - system/developer/user の責務分離、prompt object、structured outputs を検討する
  - few-shot よりまず contract と eval を整える
- Codex:
  - tool policy、verification loop、phase 分離、作業の停止条件を重視する
  - 依存関係のある作業順を崩さない

## 反映すべきアンチパターン

- 固定高得点閾値の自己採点ループ
- 内部推論の詳細出力を強制して品質担保しようとする設計
- モデル仕様の断定を、日付や出典なしで埋め込むこと
- 軽い依頼にも毎回重いレビュー様式を強制すること

## この Skill で出すと良い成果物

- 改善後プロンプト
- 実行環境別の補足
- 差分理由
- 最小テスト観点または eval 案
- 必要時のみ詳細採点
