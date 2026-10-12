# 指標JSONから成績記録まで（実装中）

## 手順

1. 一次資料で確認した財務・市場指標をJSONに入力する。確認できない数値を推定で埋めない。
2. `python3 scripts/prepare_analysis.py metrics.json payload.json` で、実装済み2.3.1採点補助関数を採点項目へ変換する。
3. `python3 scripts/record_analysis.py payload.json --dry-run` で結果を確認する。
4. 内容が正しいことを確認した後、`--dry-run` を外して記録する。
5. GitHub Actionsでテスト・CSV検証・Pages公開が成功したことを確認する。

## 実装状況

採点補助関数は `scripts/rubric_scoring.py` にあります。成長性、収益性、ROIC/資本効率、財務CF、EPS成長、バリュエーション、競争優位性、子会社/M&A、空売り需給、IR反応について、仕様書の閾値をコード化した関数を用意しています。

このパイプラインは「入力された一次資料確認済み指標の採点補助」と「記録・公開」を支援します。一次資料からの全指標の自動取得・正規化、DR/SDR、全細目の統合検証、ChatGPT分析終了時の完全自動連携は未完了です。取得不能は欠損として扱い、根拠なく補完しません。

## JSONの要件

入力は `code`, `company`, `analysis_date`, `metrics`, `buy_block_inputs` を含みます。metrics内の各グループは `scripts/rubric_scoring.py` の関数が参照するキーを使用します。数値の単位は関数のdocstringとテストに従い、比率は原則小数（20%は0.20）です。
