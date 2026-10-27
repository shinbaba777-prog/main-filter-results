# 4406 新日本理化 — 年度間照合の実測結果

## 実行結果
- GitHub Actions: https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40554514087
- ワークフロー: EDINET cross-filing checks #1 — success
- 対象: `data/edinet/extracted/financial_metric_audit.csv`
- 重複比較グループ: **133**
- 数値不一致グループ: **49**
- 比較対象外: **0行**
- 判定: `REVIEW_REQUIRED`, `scoring_ready=false`

## 重要な解釈上の制約
49件は **要調査の候補** であり、誤記・訂正・決算修正49件を意味しません。

現行照合は提出書類の期末年から相対コンテキストの年数を引いて会計年度を**推定**しています。実際のXBRLの `startDate`/`endDate`、ディメンション（連結/個別等）、タクソノミ、訂正書類を検証したものではありません。`その他` は連結と同義ではありません。

例: 売上高・推定2022年・連結区分「その他」に 28,449,000,000円 と 32,358,000,000円が混在しています。これらを同じ連結会計期間の訂正前後値とは断定できません。

## 次の検証
1. 各候補の `source_zip`・`source_csv`・`row_number` から元XBRLのコンテキスト定義を確認。
2. `startDate`・`endDate` が完全一致する行だけを年度間で比較。
3. ディメンション（連結・個別、事業セグメント等）を同一条件で比較。
4. 金額単位・符号・会計基準・訂正書類を照合。
5. 結果を監査レビュー用に出力し、承認前の正式採点を禁止。

## 保護条件
既存コード、main、Claude設定、原CSV、index.csvには手を加えず、正式採点とBUY判定を実行しません。
