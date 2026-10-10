#!/usr/bin/env python3
"""Extract EDINET XBRL CSV ZIPs into auditable long-form and candidate financial metrics.

This deliberately preserves source concepts and contexts. Candidate mappings are
heuristic and must be reviewed before use in investment scoring.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "edinet"
OUT = DATA / "extracted"
METRICS = {
    "sales": ["売上高", "営業収益", "売上収益", "Revenue", "NetSales"],
    "operating_profit": ["営業利益", "OperatingIncome"],
    "ordinary_profit": ["経常利益"],
    "profit": ["当期純利益", "親会社株主に帰属する当期純利益", "ProfitLoss"],
    "eps": ["1株当たり当期純利益", "基本的1株当たり当期利益", "EarningsPerShare"],
    "ocf": ["営業活動によるキャッシュ・フロー", "営業活動によるキャッシュフロー"],
    "icf": ["投資活動によるキャッシュ・フロー", "投資活動によるキャッシュフロー"],
    "fcf": ["フリー・キャッシュ・フロー"],
    "equity": ["純資産額", "純資産合計", "Equity"],
    "total_assets": ["資産合計", "総資産"],
    "roe": ["自己資本利益率", "ROE"],
    "roa": ["総資産利益率", "ROA"],
}
CODE_RE = re.compile(r"^(\d{4,5})_")
def clean(v):
    return (v or "").strip()
def looks_numeric(v):
    if not v:
        return False
    x = v.replace(",", "").replace("△", "-").replace("▲", "-").replace("−", "-").strip()
    return bool(re.fullmatch(r"[-+]?\(?\d+(?:\.\d+)?\)?", x))
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default="")
    args = ap.parse_args()
    zips = [Path(args.zip)] if args.zip else sorted(DATA.glob("*_xbrl_csv.zip"))
    if not zips:
        raise SystemExit("No *_xbrl_csv.zip files found in data/edinet")
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    candidates = []
    source_zips = []
    for zp in zips:
        if not zp.exists():
            print(f"Skip missing ZIP: {zp}")
            continue
        match = CODE_RE.match(zp.name)
        code = match.group(1) if match else ""
        source_zips.append(zp.name)
        with zipfile.ZipFile(zp) as zf:
            for member in zf.namelist():
                if not member.lower().endswith(".csv") or member.endswith("/"):
                    continue
                try:
                    raw = zf.read(member)
                except Exception:
                    continue
                text = None
                for enc in ("utf-8-sig", "cp932", "utf-8"):
                    try:
                        text = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        pass
                if text is None:
                    continue
                lines = text.splitlines()
                if not lines:
                    continue
                sample = "\n".join(lines[:5])
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
                except csv.Error:
                    dialect = csv.excel
                reader = csv.reader(lines, dialect)
                rows = list(reader)
                if not rows:
                    continue
                header = [clean(x) for x in rows[0]]
                # XBRL CSV formats vary. Preserve every row and infer common label/value columns.
                for row_num, row in enumerate(rows[1:], start=2):
                    padded = row + [""] * max(0, len(header) - len(row))
                    rec = {header[i] if i < len(header) and header[i] else f"column_{i+1}": clean(padded[i]) for i in range(min(len(padded), max(len(header), len(padded))))}
                    label = " | ".join([v for k, v in rec.items() if any(t in k.lower() for t in ("label", "name", "element", "concept", "項目", "科目"))])
                    if not label:
                        label = " | ".join(padded[:min(3, len(padded))])
                    value_pairs = [(k, v) for k, v in rec.items() if looks_numeric(v)]
                    if not value_pairs:
                        continue
                    # Choose last numeric cell as a candidate, retaining all cells in raw output.
                    val_col, value = value_pairs[-1]
                    record = {"security_code": code, "source_zip": zp.name, "source_csv": member, "row_number": row_num,
                              "label_or_concept": label, "value_column": val_col, "value": value,
                              "raw_row_json": json.dumps(rec, ensure_ascii=False)}
                    all_rows.append(record)
                    label_text = label + " " + " ".join(rec.keys())
                    for metric, needles in METRICS.items():
                        if any(n.lower() in label_text.lower() for n in needles):
                            candidates.append({**record, "candidate_metric": metric, "mapping_status": "REVIEW_REQUIRED"})
    long_path = OUT / "xbrl_numeric_rows.csv"
    with long_path.open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["security_code","source_zip","source_csv","row_number","label_or_concept","value_column","value","raw_row_json"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in all_rows: w.writerow({k:r.get(k,"") for k in fields})
    cand_path = OUT / "financial_metric_candidates.csv"
    with cand_path.open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["security_code","source_zip","source_csv","row_number","candidate_metric","label_or_concept","value_column","value","mapping_status","raw_row_json"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in candidates: w.writerow({k:r.get(k,"") for k in fields})
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "source_zips": source_zips,
               "numeric_rows": len(all_rows), "candidate_metric_rows": len(candidates),
               "outputs": [str(long_path.relative_to(ROOT)), str(cand_path.relative_to(ROOT))],
               "warning": "Heuristic candidate mappings only. Verify concept, period, unit, consolidation scope, and sign before investment scoring."}
    (OUT / "extraction_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
if __name__ == "__main__":
    main()
