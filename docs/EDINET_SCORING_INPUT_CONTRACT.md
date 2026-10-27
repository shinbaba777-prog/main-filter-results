# EDINET → 2.3.1: 採点入力の検証契約

この文書は **正式採点の実行許可ではありません**。既存スクリプトやClaude設定は変更しません。

## 取得段階
- `check_edinet_readiness.py --code 4406` は取得記録の整合性だけを確認します。
- `download_complete=true` は5期の数値・連結範囲・訂正・出典の正確性を保証しません。
- `scoring_ready` は常に false です。

## 入力段階
- `verify_scoring_inputs.py input.json` は `metrics`、`buy_block_inputs`、`verified_sources` を確認します。
- `verified_sources` のキーは `growth.sales_yoy` など `グループ.項目`、BUYブロックは `buy_block_inputs.roic_below_h` 形式です。
- 出典文字列が存在しても、出典の実在・発行日・値・単位・連結範囲を照合したことにはなりません。入力作成者による監査が必要です。
- 未確認値を 0 や false に置き換えないでください。既存のテンプレートに含まれる false も、未確認のまま正式採点に使用できません。
- 検証が通っても、既存 `prepare_analysis.py` および `record_verified_analysis.py --dry-run` による独立チェックが必要です。

## 自動化上の未解決点
- `verified_sources` の文字列が正しい一次資料を参照するかを機械検証する機能は未実装。
- 2.3.1の全項目に必要なEDINET以外の情報（株価、空売り、IR超過リターン、資本コスト、Baseシナリオ）を取得する処理は未実装。
- `index.csv` の自動更新は未接続。

## 変更保護
- main、既存ワークフロー、Claude関連ファイルを直接変更しない。
- 既存ファイルの修正が必要なら、事前に承認を得る。
