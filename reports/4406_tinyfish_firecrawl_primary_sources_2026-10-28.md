# 4406 新日本理化｜TinyFish＋Firecrawl一次資料照合（2026-10-28）

**用途：レビュー用の取得記録。既存の正式判定・採点結果・index.csvは変更しない。**

## 取得方法の使い分け
- **TinyFish**：公式IRライブラリの掲載文書・年度・公表日の照合、Yahoo!ファイナンスの株価ページ取得
- **Firecrawl**：公式IRライブラリの文書タイトルとPDF URL対応付け、決算短信PDFと訂正PDFの本文抽出
- **EDINET公式API**：XBRL年度・連結範囲・訂正履歴の正式照合（この回は未実施）

## 公式IRライブラリから取得した一次資料

| 対象 | 公表日 | URL |
|---|---|---|
| FY2022 決算短信 | 2022-05-12 | https://www.nj-chem.co.jp/app/upload/ir/pdf/7886c91d07b578a9668c7f24ad043e7b.pdf |
| FY2023 決算短信 | 2023-05-11 | https://www.nj-chem.co.jp/app/upload/ir/pdf/718978af9ae7b00394fcd8c898775db8.pdf |
| FY2023 **訂正** | 2023-05-18 | https://www.nj-chem.co.jp/app/upload/ir/pdf/902fa1a42a70865c4acb65e800cd039c.pdf |
| FY2024 決算短信 | 2024-05-10 | https://www.nj-chem.co.jp/app/upload/ir/pdf/9a99425afa1448d2ba95ca002fa93b69.pdf |
| FY2025 決算短信 | 2025-05-14 | https://www.nj-chem.co.jp/app/upload/ir/pdf/6c2c396ea2b7e6780721715f90b83c3a.pdf |
| FY2026 決算短信 | 2026-05-14 | https://www.nj-chem.co.jp/app/upload/ir/pdf/36433ee666c2c24d3f13cbb481af6901.pdf |
| FY2027 1Q 決算短信 | 2026-08-07 | https://www.nj-chem.co.jp/app/upload/ir/pdf/bf30d69b4797373370e8b71d03b2adf4.pdf |

一覧出典：https://www.nj-chem.co.jp/app/ir_library/settlement

## 訂正の実証（FY2023）
2023-05-18訂正PDF本文の「訂正後」欄をFirecrawlで取得：
- 営業活動によるキャッシュ・フロー：**104百万円**（訂正前173百万円）
- 投資活動によるキャッシュ・フロー：**−659百万円**（訂正前−728百万円）
- FCF＝104−659＝**−555百万円**（訂正前173−728＝−555百万円）

**採用方針：訂正前の営業CF173、投資CF−728を最新確定値として使わない。** PDF抽出の表の負数記号は崩れる場合があるため、本文「６億５千９百万円減少」及びCF計算書の△659を照合した。

## FY2026決算短信の確認
2026-05-14公式PDFの連結サマリーをFirecrawlで取得：
- 売上高32,105百万円、営業利益576百万円、経常利益547百万円、親会社株主帰属純利益597百万円
- EPS16.03円、ROE3.2%、営業CF1,643百万円、投資CF+501百万円、現金同等物期末残高5,532百万円
- 同PDFの**2027年3月期当初予想**は売上32,500百万円、営業利益800百万円、経常利益800百万円、純利益600百万円、EPS16.09円。**2026-08-07修正後予想と混同しないこと。**

PDF：https://www.nj-chem.co.jp/app/upload/ir/pdf/36433ee666c2c24d3f13cbb481af6901.pdf

## 留保・次工程
- PDF解析は自動抽出のため、複雑な表（特に貸借対照表や符号）は再照合する。
- FY2022–FY2025の各PDF本文全項目は未検証。FY2027修正後予想PDFの本文は今回未取得。
- ROIC、WACC、機関空売り、業種PER、IR超過リターンは未確定。
- EDINET候補680行の監査承認0件という既存ブロックを解除しない。
- 取得手段はChatGPT上のプラグイン。GitHub Actionsの外部サイト直接取得コードがTinyFish/Firecrawl APIを利用しているわけではない。

**作成日：2026-10-28。出典の公表日と取得日を区別。**
