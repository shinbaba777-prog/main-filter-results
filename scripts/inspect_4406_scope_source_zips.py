#!/usr/bin/env python3
"""Read source ZIP entries for 35 unresolved scope rows; do not infer consolidated scope."""
import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

SOURCE=Path("artifacts/4406_consolidation_scope_review.json")
ZIP_DIR=Path("data/edinet")
OUT=Path("artifacts/4406_scope_source_zip_evidence.json")

def inspect(review, zip_dir=ZIP_DIR):
    unresolved=review.get("unresolved_rows",[])
    if len(unresolved)!=35 or review.get("approved_rows")!=0:
        raise ValueError("Unexpected unresolved scope inventory")
    findings=[]
    for row in unresolved:
        doc=row.get("document_id","")
        source=row.get("source_csv","")
        number=row.get("row_number","")
        if not doc or not source or not number:
            raise ValueError("Missing source provenance")
        archive=zip_dir/f"44060_{doc}_xbrl_csv.zip"
        with zipfile.ZipFile(archive) as z:
            names=z.namelist()
            if source not in names:
                raise ValueError(f"Missing source CSV {source} in {archive.name}")
            data=z.read(source).decode("utf-8-sig")
            # Raw source row number may refer to a CSV physical line. Preserve it
            # as provenance, rather than assuming its offset is a parsed CSV index.
            header=next(csv.reader(io.StringIO(data)))
            context_files=[n for n in names if n.lower().endswith((".xbrl",".xml")) and
                           ("context" in n.lower() or "instance" in n.lower())]
            findings.append({"document_id":doc,"source_zip":archive.name,
                "source_csv":source,"row_number":number,
                "element_id":row.get("element_id"),"context_id":row.get("context_id"),
                "source_csv_present":True,"source_csv_columns":header[:12],
                "context_definition_file_candidates":context_files[:10],
                "status":"SOURCE_PRESENT_SCOPE_UNRESOLVED",
                "scoring_eligible":False})
    return {"security_code":"4406","status":"REVIEW_REQUIRED","scoring_eligible":False,
        "publish_to_index":False,"approved_rows":0,"source_csv_files_verified":len(findings),
        "documents":dict(Counter(x["document_id"] for x in findings)),
        "note":"Source CSV presence is proven, but the extracted XBRL-to-CSV package may not contain XML context definitions. No consolidated-scope approval.",
        "rows":findings}

def main():
    result=inspect(json.loads(SOURCE.read_text()))
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Source ZIP evidence: {result['source_csv_files_verified']} rows traced; scope approval=0")
if __name__=="__main__":main()
