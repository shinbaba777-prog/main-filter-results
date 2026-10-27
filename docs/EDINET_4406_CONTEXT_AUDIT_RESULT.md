# 4406 新日本理化 — EDINET実データ検証結果

## 実行証跡
- GitHub Actions: https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40554330652
- Job: verify-context / 2026-10-27 17:50 UTC
- 単体テスト: 5件成功
- 実データの診断: status=REVIEW_REQUIRED, scoring_ready=false

## 集計
| 項目 | 行数 |
|---|---:|
| 財務候補の監査行数 | 680 |
| 未承認 (NOT_APPROVED) | 680 |
| 連結区分未確定 (SCOPE_UNRESOLVED) | 450 |

**注意**: 450行は680行の内数であり、足し合わせません。今回のチェックで警告されなかった230行も、出典照合・正式承認を済ませたわけではありません。

## 原資料照合の順序
1. 450行の `source_zip`, `source_csv`, `row_number`, `context_id`, `element_id` を固定し、元XBRLのコンテキスト定義を確認する。
2. `連結` / `個別` / `その他` の自動推定は行わず、提出書類ごとの定義と整合するか確認する。
3. `CurrentYearDuration` 等の相対年度を提出書類の事業年度と対応付け、重複期間を除外する。
4. 通貨単位、符号、訂正書類、期末日、会計基準を確認する。
5. 監査済みデータだけを、出典と承認履歴を保持して別途2.3.1入力へ転記する。

## 安全条件
- `APPROVED` の自動付与、採点、BUY判定、index.csv更新はしない。
- 元CSV、既存のGitHub Actions、Claude設定、mainを変更しない。
- 未確認をゼロまたはfalseとして扱わない。
