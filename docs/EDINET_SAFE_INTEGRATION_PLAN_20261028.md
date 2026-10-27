# EDINET → Main Filter 2.3.1 安全統合計画 (2026-10-28)

## 変更禁止・保護対象
- main への直接コミット、既存ファイルの削除・置換は禁止。
- Claude 関連ファイル・設定・ワークフローを変更しない。
- 既存の `.github/workflows/edinet-api.yml`、`.github/workflows/pages.yml`、`scripts/record_analysis.py`、`scripts/rubric_scoring.py` は当面読み取り専用。
- 既存ファイルを編集する必要が生じたら、対象行・理由・影響・ロールバック手順を提示して承認を得る。
- Pull Request はレビュー完了までマージしない。

## 現状確認済み
- `scripts/fetch_edinet.py` は EDINET API の取得・再試行・履歴収集を実装。
- `scripts/parse_edinet_csv.py` とレビュー系スクリプトは候補抽出を実装。
- `data/edinet/verified/4406_five_year_financials.md` に2022〜2026年の財務表あり。ROICは未確認。
- `scripts/prepare_analysis.py` は出典確認済み metrics JSON から採点用 payload を生成。
- `scripts/record_verified_analysis.py` はBUYブロックとBaseシナリオ上値余地の明示を必須化。
- `index.csv` と Pages ワークフローは存在するが、EDINET収集から正式採点までの自動接続は未実装。

## 安全な追加実装の順番
1. 新規スクリプトで EDINET manifest / 抽出候補 / 検証済み指標の状態を読み取り、機械可読の readiness JSON を生成する。元ファイルは変更しない。
2. 5期・出典・単位・連結区分・訂正履歴を検証。未確認は null とし、ゼロや合格扱いしない。
3. 株価・業種PER・空売り・IR反応・WACC・Baseシナリオなど EDINET 外の必須データが揃うまで、正式採点・記録を停止する。
4. 既存の `prepare_analysis.py` → `record_verified_analysis.py --dry-run` を使い、ルーブリック・欠損規則・BUYブロックを変えず検証する。
5. 全テスト成功、正式スコアとレポート一致、既存CSV非破壊を確認後に限り、記録・Pages公開の接続を検討する。

## 受け入れ基準
- 既存の unittest 全件成功。
- Claude関連設定の差分ゼロ。
- EDINET APIキーは GitHub Secrets のみ。ログ・成果物に露出しない。
- レート制限・部分取得・訂正書類未確認を成功と誤判定しない。
- DATA-INSUFFICIENT を BUY に昇格させない。
- index.csv の既存行・列・ソート要件を保持する。
- 本ブランチの変更は PR でレビューし、承認前は main に反映しない。

## 未解決
- 最新のEDINET API実行ログと manifest の整合性。
- 財務データの全年度・全コンテキスト監査。
- EDINET以外の外部データの取得元と利用条件。
- 自動採点後の GitHub Pages の起動経路。
