# 4406 原XBRL照合：統合テスト結果と実取得の前提

## 確認済み（GitHub Actions）

- 実行: https://github.com/shinbaba777-prog/main-filter-results/actions/runs/40575112553
- `EDINET original evidence integration checks #1`: **success**
- `test_original_json_connects_to_audit`: **ok**
- `test_missing_original_evidence_fails_closed`: **ok**
- `Fetch and check original contexts only on explicit opt-in`: **skipped**
- `Upload temporary context evidence`: **skipped**
- EDINET APIの実アクセス: **未実施**
- 4406の680行に対する原XBRL照合: **未実施**
- 採点承認: **0行**

## 実行上のブロッカー

1. 取得処理は `EDINET_API_KEY` をGitHub ActionsのSecretsから読み取る。キーはリポジトリへコミットしない。
2. 新規の `workflow_dispatch` ワークフローは作業ブランチだけにある。GitHubの手動実行一覧に表示されるとは限らないため、表示・実行可能であると断定しない。
3. 現在のGitHub接続ツールにはワークフローの新規手動実行アクションがない。既存の実行履歴を読むことは可能。
4. `--check-audit` はコンテキストIDの存在を検査する。元XBRLの同一書類内での複数インスタンス・同名ID、会計期間、連結区分、タクソノミ、単位、符号の正しさを完全に認定するものではない。
5. 既存の `.github/workflows/edinet-api.yml` は `type=5` のCSV ZIPを取得する。原XBRL取得には別途 `type=1` が必要。

## 次に実行すべき工程

1. 作業ブランチの統合テスト成功を維持する。
2. 原XBRL取得用ワークフローを**承認済みの方法で実行可能にする**。既存のmainやClaude設定を無断変更しない。
3. EDINET APIから対象5書類（S100OK43、S100R83V、S100TUAP、S100W17N、S100YGXD）の原XBRLを取得し、コンテキスト証拠を一時アーティファクトに保存する。
4. 680行の監査候補と照合し、未確認・不一致・複数インスタンスの曖昧性を分類する。
5. 原XBRLの事実検証を経て初めて5年分の財務表の確定作業に進む。

**禁止**: 原XBRL未確認のまま `scoring_ready=true` とすること、メインフィルター2.3.1のBUY判定、`index.csv`更新、`main`への無断マージ。
