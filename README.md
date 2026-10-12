# 日本株メインフィルター分析結果

このリポジトリは、メインフィルターによる日本株分析結果を保存・管理するためのリポジトリです。

## 自動記録運用

今後、ChatGPTで日本株を**メインフィルターで正式分析した場合、その分析結果をこのリポジトリの `index.csv` に1件追加する**運用にします。

### 追加ルール

- 1銘柄の正式分析 = 1レコード
- 過去のレコードは、後からメインフィルターの新バージョンが出ても自動で再採点しない
- 分析時点の `filter_version` をそのまま保存
- 分析日・スコア・STAGE1・判定・主要コメントを保存
- 次回決算日が確認できた場合は `earnings_date` / `earnings_text` に保存
- 確認できない数値は推定せず、空欄・「欠損」・「未確認」等で記録
- 同一銘柄を別日に再分析した場合は、原則として**新しい1レコード**として追加
- 既存レコードを書き換えるのは、明確な訂正・入力ミス修正などの場合のみ

## index.csv

`index.csv` が記録データの正本です。

現在の基本項目：

```
code,company,analysis_date,filter_version,score,stage1,judgment,notes,earnings_date,earnings_text,holding
```

将来的に分析価格、3か月・6か月・12か月確認日、確認時株価などを追加できます。

## Webページ

GitHub Pagesは `index.csv` から公開ページを自動生成します。

- 1ページ50件表示
- 銘柄名・コード検索
- 確認待ち / 保有中フィルター
- 日付の新しい順
- スコアの高い順
- 次回決算が近い順
- ページ送り
- 全件を対象にした集計

したがって、記録が**2,000件程度まで増えても、1ページに全件を描画しない**ため軽快に利用できます。

## 現行基準

- 現行基準：メインフィルター2.3.1
- 分析結果は銘柄コード・分析日単位で管理
- 後から再評価できるよう、分析時点の結果を残す
- 数値が確認できない場合は推定せず「欠損」「未確認」等で記録

## ディレクトリ構成

```
/
├── README.md
├── index.csv
├── index.html
├── scripts/
│   └── generate_index.py
├── .github/
│   └── workflows/
│       └── pages.yml
└── results/
    └── （銘柄別の分析結果）
```

## 今後の運用

今後、ユーザーが「○○をメインフィルター2.3.1で正式採点」などと依頼した場合は、

**① 最新情報を調査 → ② 正式採点 → ③ 結果を確認 → ④ `index.csv` に新規レコード追加 → ⑤ GitHub Pages自動更新**

までを一連の運用として扱います。

投資判断そのものは、最新の開示資料・市場データ等を確認したうえで行います。


## EDINETデータ取得・レビュー

EDINET APIによる提出書類取得、XBRL CSV抽出、候補検証、レビューキューの使い方と安全上の注意は [`EDINET_REVIEW_GUIDE.md`](EDINET_REVIEW_GUIDE.md) を参照してください。抽出候補は自動承認せず、一次資料と照合するまで正式採点には使用しません。


## メインフィルター2.3.1の統合プロトコル

データ取得から検証・採点・成績記録までの標準手順は [MAIN_FILTER_2.3.1_INTEGRATION.md](MAIN_FILTER_2.3.1_INTEGRATION.md) に定義しています。既存の配点・STAGE 1通過条件・欠損ルール・BUYブロックは変更しません。

重要：EDINET抽出候補は未検証のまま採点に使用しません。候補件数を欠損指標数と同一視せず、一次資料と照合できた値のみ採点に使用します。正式採点完了後に index.csv へ記録し、Pagesデプロイ成功まで確認します。

現時点で実装済み：採点入力の検証、2.3.1の配点グループ集計・欠損調整・STAGE 1判定・BUY強制ブロック、ユニットテスト、`analysis.json` から `index.csv` への重複防止付き記録、GitHub Pages自動公開です。\n\n未完了：決算短信・有報・株価・JPX業種PER・空売り・IR反応などを自動取得し、各採点細目の点数まで一次資料に基づき自動算出するデータ取得／指標計算層、およびChatGPTの分析完了時に入力JSONを自動生成してGitHubへ渡す連携です。採点入力JSONの雛形は [`examples/analysis_payload.template.json`](examples/analysis_payload.template.json)、記録コマンドは [`scripts/record_analysis.py`](scripts/record_analysis.py) です。現状は、検証済みの点数入力がなければエンジンが独自に財務数値や点数を推測することはありません。

## EDINET 5期データの手動取得

1. [EDINET API data refresh](https://github.com/shinbaba777-prog/main-filter-results/actions/workflows/edinet-api.yml) を開く。
2. **Run workflow** を押す。
3. `securities_code` に対象銘柄コードを入力する（例: `4406`）。
4. `download_history` を有効にして実行する。
5. 実行完了後、Actions の実行詳細にある Artifacts から `edinet-review-<run_id>` をダウンロードする。

この工程はEDINETの財務事実候補とレビューキューを作るもので、正式採点を自動確定するものではありません。抽出値は有価証券報告書の期間・連結範囲・単位・訂正有無・重複などを確認してから承認してください。市場PER、株価、空売り、IR反応、ROIC-WACC、BUYブロック条件が未確認のままなら、正式なBUY判定や数値スコアの確定は行いません。
