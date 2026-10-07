#!/usr/bin/env python3
import csv, json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "index.csv"
OUT = ROOT / "index.html"

with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

records = []
for r in rows:
    records.append({
        "code": r.get("code",""),
        "company": r.get("company",""),
        "analysis_date": r.get("analysis_date",""),
        "filter_version": r.get("filter_version",""),
        "score": r.get("score",""),
        "stage1": r.get("stage1",""),
        "judgment": r.get("judgment",""),
        "notes": r.get("notes",""),
        "earnings_date": r.get("earnings_date",""),
        "earnings_text": r.get("earnings_text",""),
        "holding": r.get("holding","false").lower() == "true",
    })

data = json.dumps(records, ensure_ascii=False, separators=(",",":"))

template = r'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>フィルター成績記録</title>
<style>
body{margin:0;background:#f5f7fb;color:#172033;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans JP",sans-serif}
.wrap{max-width:900px;margin:auto;padding:24px 16px}
h1{font-size:30px;margin:8px 0 12px}.count{color:#778095;font-size:13px;margin-bottom:18px}
.tabs{display:flex;gap:28px;border-bottom:1px solid #e7eaf0;margin-bottom:14px}.tab{border:0;background:none;padding:0 0 12px;font:inherit;font-weight:800;color:#778095;cursor:pointer}.tab.active{color:#172033;border-bottom:3px solid #172033}
.controls{display:grid;gap:10px;margin-bottom:14px}.search{width:100%;box-sizing:border-box;border:1px solid #dfe3ea;border-radius:10px;padding:12px 13px;background:#fff;font-size:14px}
.pills,.sorts,.pager{display:flex;gap:7px;flex-wrap:wrap}.pill,.sort,.pagebtn{border:1px solid #dfe3ea;background:#fff;color:#4d5668;border-radius:9px;padding:8px 11px;font-size:12px;font-weight:700;cursor:pointer}.pill{border-radius:999px}.pill.active,.sort.active,.pagebtn.active{background:#172033;color:#fff;border-color:#172033}.pagebtn:disabled{opacity:.45;cursor:default}
.card{background:#fff;border:1px solid #e7eaf0;border-radius:14px;padding:16px;margin:10px 0}.top{display:flex;justify-content:space-between;gap:10px}.name{font-weight:800;font-size:16px}.code,.date{color:#778095;font-size:12px;margin-left:8px}
.status{display:inline-block;margin-top:8px;padding:5px 9px;border-radius:7px;font-size:12px;font-weight:800;background:#fff6df;color:#9a6b00}.status.gray{background:#f2f4f7;color:#4d5668}
.reason{font-size:12px;color:#606a7b;margin-top:8px;line-height:1.55}.meta{font-size:11px;color:#8992a2;margin-top:7px}.earnings{font-size:12px;color:#172033;margin-top:10px;font-weight:800}.earnings span{font-weight:600;color:#606a7b}.earnings-alert{display:inline-block;margin-left:7px;padding:2px 6px;border-radius:999px;font-size:10px;font-weight:800;background:#fff0f0;color:#b42318}.earnings-soon{background:#fff7df;color:#9a6700}
.score{font-size:27px;font-weight:900;margin-top:14px}.score small{font-size:13px}.summary{display:none;background:#fff;border:1px solid #e7eaf0;border-radius:14px;padding:16px;margin-top:10px}.summary.show{display:block}.empty{text-align:center;color:#778095;padding:30px 10px;display:none}.pager{justify-content:center;margin:16px 0 6px}
@media(max-width:520px){h1{font-size:29px}.wrap{padding:22px 14px}.top{align-items:flex-start}.date{white-space:nowrap}}
</style>
</head>
<body>
<main class="wrap">
<h1>フィルター成績記録</h1>
<div class="count" id="count"></div>
<div class="tabs"><button class="tab active" id="recordsTab" type="button">記録</button><button class="tab" id="summaryTab" type="button">集計</button></div>
<section id="recordsView">
<div class="controls">
<input class="search" id="search" type="search" placeholder="銘柄名・コードで検索（例:4019、スタメン）">
<div class="pills"><button class="pill active" data-filter="all" type="button">すべて</button><button class="pill" data-filter="pending" type="button">確認待ち</button><button class="pill" data-filter="holding" type="button">保有中</button></div>
<div class="sorts"><button class="sort active" data-sort="date" type="button">日付の新しい順</button><button class="sort" data-sort="score" type="button">スコアの高い順</button><button class="sort" data-sort="earnings" type="button">次回決算が近い順</button></div>
</div>
<section id="cards"></section>
<div class="empty" id="empty">該当する記録はありません。</div>
<div class="pager"><button class="pagebtn" id="prev" type="button">前へ</button><span id="pages"></span><button class="pagebtn" id="next" type="button">次へ</button></div>
</section>
<section class="summary" id="summaryView"><strong>集計</strong><div id="summaryText" style="margin-top:10px;color:#606a7b;font-size:13px;line-height:1.8"></div></section>
</main>
<script>
const records = __DATA__;
(function(){
 const PAGE_SIZE=50;
 const cardsBox=document.getElementById("cards"), search=document.getElementById("search"), count=document.getElementById("count"), empty=document.getElementById("empty");
 const prev=document.getElementById("prev"), next=document.getElementById("next"), pages=document.getElementById("pages");
 let filter="all", sort="date", page=1;
 const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",""":"&quot;","'":"&#39;"}[c]));
 function pending(r){return !r.score || (r.judgment||"").includes("DATA-INSUFFICIENT") || (r.judgment||"").includes("判定不能") || (r.judgment||"").includes("確認待ち");}
 function filtered(){
  const q=search.value.trim().toLowerCase();
  let a=records.filter(r=>{const hit=!q||(r.company+" "+r.code).toLowerCase().includes(q); const p=pending(r); return hit&&(filter==="all"||(filter==="pending"&&p)||(filter==="holding"&&!p));});
  a.sort((x,y)=>{
   if(sort==="score"){const xs=parseFloat(x.score),ys=parseFloat(y.score);if(isNaN(xs)&&isNaN(ys))return 0;if(isNaN(xs))return 1;if(isNaN(ys))return -1;return ys-xs;}
   if(sort==="earnings"){if(!x.earnings_date&&!y.earnings_date)return 0;if(!x.earnings_date)return 1;if(!y.earnings_date)return -1;return x.earnings_date.localeCompare(y.earnings_date);}
   return (y.analysis_date||"").localeCompare(x.analysis_date||"");
  }); return a;
 }
 function earningsHtml(r){
  if(!r.earnings_text&&!r.earnings_date)return "";
  let extra="";
  if(r.earnings_date){const d=new Date(r.earnings_date+"T00:00:00"), t=new Date();t.setHours(0,0,0,0);const n=Math.ceil((d-t)/86400000);if(n<0)extra='<span>（決算済み）</span>';else if(n<=7)extra='<span class="earnings-alert">（あと'+n+'日）</span>';else if(n<=30)extra='<span class="earnings-alert earnings-soon">（あと'+n+'日）</span>';else extra='<span>（あと'+n+'日）</span>';}
  return '<div class="earnings">次回決算：<span>'+esc(r.earnings_text||r.earnings_date)+'</span>'+extra+'</div>';
 }
 function render(){
  const a=filtered(), total=a.length, max=Math.max(1,Math.ceil(total/PAGE_SIZE)); if(page>max)page=max;
  const start=(page-1)*PAGE_SIZE; const view=a.slice(start,start+PAGE_SIZE);
  cardsBox.innerHTML=view.map(r=>'<article class="card"><div class="top"><div><span class="name">'+esc(r.company)+'</span><span class="code">'+esc(r.code)+'</span><br><span class="status '+(pending(r)?"gray":"")+'">'+esc(r.judgment||"—")+'</span></div><span class="date">'+esc(r.analysis_date)+'</span></div><div class="reason">'+esc(r.notes||"")+'</div>'+earningsHtml(r)+'<div class="meta">フィルター '+esc(r.filter_version||"—")+(r.stage1?" ／ STAGE1 "+esc(r.stage1):"")+'</div><div class="score">'+esc(r.score||"—")+' <small>点</small></div></article>').join("");
  empty.style.display=total?"none":"block"; count.textContent="記録 "+records.length+" 件　確認待ち "+records.filter(pending).length+" 件";
  prev.disabled=page<=1; next.disabled=page>=max; pages.innerHTML="";
  for(let i=1;i<=max&&i<=9;i++){const b=document.createElement("button");b.className="pagebtn"+(i===page?" active":"");b.textContent=i;b.onclick=()=>{page=i;render();window.scrollTo(0,0)};pages.appendChild(b);}
  updateSummary();
 }
 function updateSummary(){const scored=records.map(r=>parseFloat(r.score)).filter(n=>!isNaN(n));const avg=scored.length?(scored.reduce((a,b)=>a+b,0)/scored.length).toFixed(1):"—";document.getElementById("summaryText").textContent="総記録 "+records.length+" 件 ／ スコア確認済み "+scored.length+" 件 ／ 平均スコア "+avg+" 点 ／ 1ページ "+PAGE_SIZE+" 件";}
 search.oninput=()=>{page=1;render()}; prev.onclick=()=>{if(page>1){page--;render();window.scrollTo(0,0)}}; next.onclick=()=>{page++;render();window.scrollTo(0,0)};
 document.querySelectorAll(".pill").forEach(b=>b.onclick=()=>{document.querySelectorAll(".pill").forEach(x=>x.classList.remove("active"));b.classList.add("active");filter=b.dataset.filter;page=1;render()});
 document.querySelectorAll(".sort").forEach(b=>b.onclick=()=>{document.querySelectorAll(".sort").forEach(x=>x.classList.remove("active"));b.classList.add("active");sort=b.dataset.sort;page=1;render()});
 recordsTab.onclick=()=>{recordsTab.classList.add("active");summaryTab.classList.remove("active");recordsView.style.display="block";summaryView.classList.remove("show")};
 summaryTab.onclick=()=>{summaryTab.classList.add("active");recordsTab.classList.remove("active");recordsView.style.display="none";summaryView.classList.add("show");updateSummary()};
 render();
})();
</script>
</body>
</html>
'''
OUT.write_text(template.replace("__DATA__", data), encoding="utf-8")
print(f"generated {OUT} with {len(records)} records")
