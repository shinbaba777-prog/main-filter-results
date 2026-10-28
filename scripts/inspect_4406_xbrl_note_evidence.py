#!/usr/bin/env python3
"""Review-only original XBRL note and extension evidence for lease/bond/equity scope."""
import io
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

PATTERN = re.compile(r"lease|リース|bond|社債|commercial.paper|コマーシャル.?ペーパー|subscription.right|新株予約権|interest.bearing|有利子負債|other.current.liabilit|その他流動負債|other.noncurrent.liabilit|その他固定負債",re.I)
INSTANCE="{http://www.xbrl.org/2003/instance}"
MAX_BYTES=20_000_000
MAX_MATCHES=1000

def inspect(payload,doc_id):
    if not zipfile.is_zipfile(io.BytesIO(payload)):
        raise ValueError("Original filing is not ZIP")
    matches=[]
    files=[]
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        for member in z.infolist():
            path=member.filename
            if not path.lower().endswith((".xbrl",".xml")) or "publicdoc" not in path.lower():
                continue
            if member.file_size>MAX_BYTES:
                raise ValueError("Oversized XBRL/XML; review required")
            root=ET.fromstring(z.read(member))
            files.append(path)
            for node in root.iter():
                tag=node.tag.rsplit("}",1)[-1]
                if node.get("contextRef"):
                    value=" ".join(node.itertext()).strip()
                    # Only concise matching text excerpts. No assertion that unlisted concepts are zero.
                    if PATTERN.search(tag) or (not node.get("unitRef") and PATTERN.search(value)):
                        excerpt=value[:420]
                        matches.append({"file":path,"concept":tag,"context_id":node.get("contextRef"),
                                        "unit_ref":node.get("unitRef"),"excerpt":excerpt,
                                        "match_basis":"concept" if PATTERN.search(tag) else "note_text"})
                elif tag in ("label","definition","documentation","loc","arc"):
                    text=" ".join(node.itertext()).strip()
                    href=node.get("{http://www.w3.org/1999/xlink}href","")
                    if PATTERN.search(text) or PATTERN.search(href):
                        matches.append({"file":path,"element":tag,"label":text[:220],"href":href[:300]})
                if len(matches)>MAX_MATCHES:
                    raise ValueError("Evidence cap reached; manual review required")
    return {"document_id":doc_id,"files_inspected":len(files),"match_count":len(matches),
            "matches":matches,"scoring_eligible":False,"publish_to_index":False,"approved_rows":0}

def save(documents,path):
    result={"status":"NOTE_AND_TAXONOMY_REVIEW_REQUIRED","documents":documents,
            "scoring_eligible":False,"publish_to_index":False,"approved_rows":0}
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+chr(10),encoding="utf-8")
    return result
