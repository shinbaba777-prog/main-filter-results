# EDINETデータ運用・レビュー手順

## 現在の自動処理

GitHub Actions の **EDINET API data refresh** が、EDINET API v2から提出書類メタデータを取得し、指定銘柄の年次有価証券報告書CSV ZIPを保存します。XBRL CSVを抽出し、候補行の構造検査とレビューキュー作成を実行します。

- 自動取得の対象：提出書類メタデータ
- 手動実行で指定できる対象：証券コード、CSV取得、最大5期の履歴取得
- 保存先：`data/edinet/`
- 候補レビューキュー：`data/edinet/extracted/core_metric_review_queue.csv`
- 候補の構造監査：`data/edinet/extracted/financial_metric_audit.csv`
- 各処理の集計：同じ `extracted/` 内の `*_summary.json`

## 重要：自動承認・自動採点はしない

抽出値は投資判断にそのまま使える確定値ではありません。候補には、連結/個別の範囲、会計基準、期間、単位・倍率、符号、訂正報告、同一事実の重複、要素IDの定義確認が必要な行が含まれます。構造検査を通った行も「投資採点に使用可能」とは限りません。

このため、この処理は `index.csv` を変更せず、メインフィルター2.3.1のスコアやBUY/HOLD判定を自動生成しません。レビュー済みの値だけを、一次資料と照合したうえで正式分析に使用します。

## 手動レビュー手順

1. [最新のActions実行履歴](https://github.com/shinbaba777-prog/main-filter-results/actions/workflows/edinet-api.yml)を開き、最新実行が成功していることを確認します。
2. [ダウンロードマニフェスト](https://github.com/shinbaba777-prog/main-filter-results/blob/main/data/edinet/download_manifest.json)で、対象期がそろっているか、`gaps` と `failed_scan_dates` が空かを確認します。
3. [抽出サマリー](https://github.com/shinbaba777-prog/main-filter-results/blob/main/data/edinet/extracted/extraction_summary.json)で、ZIP一覧・数値行数・候補行数・スキップされたCSVがないかを確認します。
4. [主要指標レビューキュー](https://github.com/shinbaba777-prog/main-filter-results/blob/main/data/edinet/extracted/core_metric_review_queue.csv)で候補行を確認し、元CSVの行、要素ID、コンテキスト、対象期、連結/個別、単位、符号を有価証券報告書と照合します。
5. [構造監査サマリー](https://github.com/shinbaba777-prog/main-filter-results/blob/main/data/edinet/extracted/financial_metric_audit_summary.json)の警告とフラグを確認します。警告を解消できない値は「欠損/未確認」とし、推定で補いません。
6. 公式開示と照合できた場合でも、株価・PER・業種比較・ROIC/WACC・空売り・希薄化など、メインフィルターが要求する他の情報を別途確認してから採点します。

## 実行方法

1. GitHubリポジトリの **Actions → EDINET API data refresh → Run workflow** を開きます。
2. 1銘柄の直近書類を試す場合は証券コード（例：`4406`）とCSV取得を指定します。
3. 5期履歴を調べる場合は証券コードを入力し、履歴取得を指定します。
4. APIキーは `Settings → Secrets and variables → Actions` の `EDINET_API_KEY` にだけ保存します。チャット、コード、公開ファイルに貼り付けないでください。

## 完了条件

- Actionsの取得・抽出・検証・レビューキュー作成が成功
- マニフェストの期・欠落・取得失敗を確認
- 出力ファイルとサマリーが保存済み
- 正式採点に使う値は一次資料と照合済み
- 未確認の候補値が `index.csv` や正式スコアに自動混入しない

前半4つの自動処理は繰り返し実行できます。最後の一次資料照合と投資判断は、誤採点防止のため別工程です。
