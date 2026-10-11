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

# Exact XBRL element IDs are candidate mappings only; all remain review-required.
ELEMENT_METRICS = {
    "jppfs_cor:NetSales": "sales",
    "jpcrp_cor:NetSalesSummaryOfBusinessResults": "sales",
    "jppfs_cor:OperatingIncome": "operating_profit",
    "jpigp_cor:OperatingProfitLossIFRS": "operating_profit",
    "jpcrp_cor:OperatingIncomeLossUSGAAPSummaryOfBusinessResults": "operating_profit",
    "jppfs_cor:OrdinaryIncome": "ordinary_profit",
    "jpcrp_cor:OrdinaryIncomeLossSummaryOfBusinessResults": "ordinary_profit",
    "jppfs_cor:ProfitLoss": "profit",
    "jpcrp_cor:NetIncomeLossSummaryOfBusinessResults": "profit",
    "jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults": "profit",
    "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults": "eps",
    "jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults": "ocf",
    "jppfs_cor:NetCashProvidedByUsedInOperatingActivities": "ocf",
    "jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults": "icf",
    "jppfs_cor:NetCashProvidedByUsedInInvestmentActivities": "icf",
}
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
CODE_RE = re.compile(r"^([0-9][0-9A-Z][0-9][0-9A-Z][0-9A-Z]?)_")
def clean(v):
    return (v or "").strip()
def normalize_numeric(v):
    if not v:
        return ""
    x = v.strip().replace("，", ",").replace(",", "")
    x = x.replace("△", "-").replace("▲", "-").replace("−", "-").replace("－", "-")
    x = x.replace("（", "(").replace("）", ")").replace("％", "%").replace("　", "")
    # EDINET CSVs may contain full-width digits and accounting-style parentheses.
    x = x.translate(str.maketrans("０１２３４５６７８９．＋", "0123456789.+"))
    x = x.strip()
    if x.startswith("(") and x.endswith(")"):
        x = "-" + x[1:-1]
    return x

def looks_numeric(v):
    x = normalize_numeric(v)
    return bool(x and re.fullmatch(r"[-+]?\d+(?:\.\d+)?%?", x))
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default="")
    ap.add_argument("--allow-incomplete", action="store_true", help="Allow parsing a manifest marked incomplete for diagnostics only")
    args = ap.parse_args()
    manifest_path = DATA / "download_manifest.json"
    manifest = None
    if not args.zip:
        if not manifest_path.exists():
            raise SystemExit("Missing download_manifest.json; refusing to glob old ZIP files")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") not in ("complete", "complete_short_history") and not args.allow_incomplete:
            raise SystemExit("Download manifest is incomplete; extraction refused. Use --allow-incomplete for diagnostics only.")
        zips = [DATA / item["file"] for item in manifest.get("periods", []) if item.get("status") == "downloaded" and item.get("file")]
    else:
        zips = [Path(args.zip)]
    if not zips:
        raise SystemExit("No *_xbrl_csv.zip files found in data/edinet")
    OUT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    candidates = []
    source_zips = []
    skipped_csv_members = []
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
                except Exception as exc:
                    skipped_csv_members.append({"zip": zp.name, "member": member, "reason": "read_error:" + type(exc).__name__})
                    continue
                text = None
                for enc in ("utf-16", "utf-16-le", "utf-8-sig", "cp932", "utf-8"):
                    try:
                        text = raw.decode(enc)
                        break
                    except UnicodeDecodeError:
                        pass
                if text is None:
                    skipped_csv_members.append({"zip": zp.name, "member": member, "reason": "decode_error"})
                    continue
                lines = text.splitlines()
                if not lines:
                    skipped_csv_members.append({"zip": zp.name, "member": member, "reason": "empty_csv"})
                    continue
                sample = "\n".join(lines[:8])
                # Sniffer can misidentify EDINET delimiters when the sample is sparse.
                # Try common delimiters and select the parse with the most columns.
                parsed_options = []
                for delimiter in ("\t", ",", ";", "|"):
                    try:
                        parsed = list(csv.reader(lines, delimiter=delimiter))
                        width = max((len(r) for r in parsed[:20]), default=0)
                        parsed_options.append((width, parsed))
                    except csv.Error:
                        pass
                rows = max(parsed_options, key=lambda item: item[0])[1] if parsed_options else list(csv.reader(lines))
                if rows and max(len(r) for r in rows[:20]) <= 1:
                    print(f"CSV_DIAGNOSTIC member={member!r} delimiter_parse_single_column=True sample={lines[:3]!r}")
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
                    value_pairs = [(k, normalize_numeric(v)) for k, v in rec.items() if looks_numeric(v)]
                    if not value_pairs:
                        continue
                    # Choose last numeric cell as a candidate, retaining all cells in raw output.
                    val_col, value = value_pairs[-1]
                    record = {"security_code": code, "source_zip": zp.name, "source_csv": member, "row_number": row_num,
                              "label_or_concept": label, "value_column": val_col, "value": value,
                              "raw_row_json": json.dumps(rec, ensure_ascii=False)}
                    all_rows.append(record)
                    label_text = label + " " + " ".join(rec.keys())
                    concept = clean(rec.get("要素ID", ""))
                    exact_metric = ELEMENT_METRICS.get(concept)
                    if exact_metric:
                        candidates.append({**record, "candidate_metric": exact_metric,
                                           "mapping_status": "EXACT_ELEMENT_ID_REVIEW_REQUIRED"})
                    else:
                        # Avoid classifying individual cash-flow line items as total OCF/ICF.
                        # The total cash-flow concepts are mapped above by exact element ID.
                        is_cashflow_component = concept.endswith("OpeCF") or concept.endswith("InvCF") or concept.endswith("FinCF")
                        for metric, needles in METRICS.items():
                            if is_cashflow_component and metric in ("ocf", "icf", "fcf"):
                                continue
                            if any(n.lower() in label_text.lower() for n in needles):
                                candidates.append({**record, "candidate_metric": metric,
                                                   "mapping_status": "HEURISTIC_REVIEW_REQUIRED"})
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
    if source_zips and not all_rows:
        print("EXTRACTION_DIAGNOSTIC: no numeric rows detected; inspecting CSV members and sample rows.")
        for zp in zips:
            if not zp.exists():
                continue
            with zipfile.ZipFile(zp) as zf:
                csv_members = [n for n in zf.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
                print(f"ZIP_DIAGNOSTIC zip={zp.name!r} csv_members={len(csv_members)} names={csv_members[:12]!r}")
                for member in csv_members[:2]:
                    raw = zf.read(member)
                    preview = raw[:1200].decode("utf-16", errors="replace") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in raw[:80] else raw[:1200].decode("utf-8-sig", errors="replace")
                    print(f"CSV_PREVIEW member={member!r} preview={preview[:1200]!r}")
    summary = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "source_zips": source_zips,
               "numeric_rows": len(all_rows), "candidate_metric_rows": len(candidates),
               "skipped_csv_members": skipped_csv_members,
               "fiscal_periods": (manifest.get("periods", []) if manifest else []),
               "amendments": (manifest.get("amendments", []) if manifest else []),
               "outputs": [str(long_path.relative_to(ROOT)), str(cand_path.relative_to(ROOT))],
               "warning": "Heuristic candidate mappings only. Verify concept, period, unit, consolidation scope, and sign before investment scoring."}
    (OUT / "extraction_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    if skipped_csv_members:
        raise SystemExit(3)
if __name__ == "__main__":
    main()
