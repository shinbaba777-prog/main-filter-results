# メインフィルター2.3.1 出典管理・自動取得仕様（提案／未マージ）

## 保護方針
- 既存の `main`、Claude関連設定、EDINET取得コード、採点ロジック、`index.csv` は変更しない。
- 4406で検証後に段階的に適用する。データ未取得・未検証をゼロ点に置き換えない。
- 出典がない指標は正式採点に使用しない。出典は数値ごとに追跡可能とする。

## データ取得の優先順位
| 指標 | 一次取得先 | 補助・照合先 | 留意点 |
| --- | --- | --- | --- |
| 有報・5期財務・BS・CF | EDINETの保存済み原本 | 会社IR、IR BANK | 連結/個別、期間、単位、訂正報告書を検証 |
| 決算予想・修正・イベント | 会社IR・TDnet | Yahoo!ファイナンス | 公表時刻と更新日を記録 |
| 日次株価・PER・PBR | 取引所公表情報・利用可能な正規データ提供元 | Yahoo!ファイナンス | 取得条件・利用規約を遵守、調整株価と基準日を明示 |
| 業種PER・指数 | JPX | - | 対象市場・業種・集計月を明示 |
| 空売り公表残高 | JPX公表情報 | - | 0.5%閾値、90日非該当、報告日と計算日を区別 |
| 企業の過去指標 | EDINET・会社IR | IR BANK | IR BANKは照合用。取得不可なら推定しない |
| IR後5営業日超過収益 | 株価・指数の日次データ | - | 公表日、対象5営業日、基準指数を保存 |

## 指標ごとの証跡（必須）
```json
{
  "security_code": "4406",
  "metric": "operating_profit",
  "value": 576,
  "unit": "JPY million",
  "fiscal_period_end": "2026-03-31",
  "consolidation": "consolidated",
  "source_name": "EDINET",
  "source_document": "2026年3月期 有価証券報告書",
  "source_url": "https://disclosure2.edinet-fsa.go.jp/",
  "document_id": "S100YGXD",
  "retrieved_at_utc": null,
  "published_at": null,
  "verification_status": "SOURCE_VERIFIED",
  "calculation": null,
  "notes": "既存の5期財務検証台帳と照合。実際の文書URL・取得日時は処理時に確定"
}
```
上記は構造例であり、`retrieved_at_utc` や文書の直接URLを取得した事実を示さない。

## レポート必須セクション
1. 判定基準日・フィルター版・データ鮮度
2. STAGE1/2細目ごとの得点、欠損・非該当・固定0の区別
3. 各採点指標の出典名、文書名、文書IDまたはURL、対象期、取得日時、検証状態
4. CAGR/ROIC/FCF/PEG/ネットデット等の式・入力値・出典への参照
5. BUYブロックと未判定理由
6. 「出典・参照資料一覧」（重複URLはまとめてよいが指標との対応を残す）

## 安全ゲート
- XBRL候補行の自動採点は禁止。レビューキューの`APPROVED`のみ下流候補にできる。
- 正式スコアに必要な欠損点数とSTAGE1通過条件は既存正本・エンジンに従う。
- Yahoo!ファイナンス、IR BANK等で取得が技術的・契約的に許されない場合、代替ソースへ切替または`取得不可`。
- GitHub Actionsのログ・出力にAPIキーや秘密情報を含めない。
- 検証完了前に`index.csv`を上書きしない。
