#!/usr/bin/env python3
"""Initial FINAR-VL financial data synthesis from data/raw using local model/qwen235."""
from __future__ import annotations

import argparse, ast, csv, hashlib, json, os, random, re, subprocess, sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
OUT_ROOT = PROJECT_ROOT / "data" / "synthetic" / "finance_world"
EXTRACT_MODEL = str(PROJECT_ROOT / "model" / "qwen32")
CONSTRUCT_MODEL = str(PROJECT_ROOT / "model" / "qwen235")
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
SUPERVISION = {"question","questions","answer","answers","solution","cot","reasoning","rationale","label","labels","target","program","prompt","instruction","choices","options","messages","conversation","conversations"}
IMAGE_KEYS = {"image","images","image_path","image_paths","media","media_paths"}
CONTEXT = {"context","reference","references","passage","document","doc","text","pre_text","post_text","paragraphs","table","tables","table_ori","report","filing","article","ocr","ocr_text","source_text"}
NUM_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
YEAR_RE = re.compile(r"(?<!\d)(20\d{2})(?:年|年度)?")
TICKER_RE = re.compile(r"(?<!\d)([03689]\d{5})(?!\d)")
COMPANY_RE = re.compile(r"([\u4e00-\u9fffA-Za-z0-9（）()·-]{2,50}(?:股份有限公司|集团有限公司|银行股份有限公司|证券股份有限公司|有限公司))")
VALUE_RE = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?\s*(?:%|％|亿元|亿美元|百万元|百万美元|万元|千元|人民币元|美元|港元|元|万股|亿股|股|倍|bps|bp|基点)?", re.I)
METRICS = {
    "revenue": ("营业收入","营业总收入","营收","revenue","operating revenue"),
    "gross_profit": ("毛利润","毛利","gross profit"),
    "net_profit": ("净利润","net profit","net income"),
    "attributable_net_profit": ("归属于母公司股东的净利润","归母净利润","net profit attributable"),
    "operating_cash_flow": ("经营活动产生的现金流量净额","经营现金流","operating cash flow"),
    "total_assets": ("资产总额","总资产","total assets"),
    "current_assets": ("流动资产合计","流动资产","current assets"),
    "total_liabilities": ("负债总额","总负债","total liabilities"),
    "current_liabilities": ("流动负债合计","流动负债","current liabilities"),
    "equity": ("所有者权益合计","股东权益合计","净资产","total equity","shareholders' equity"),
    "inventory": ("存货","inventory"), "accounts_receivable": ("应收账款","accounts receivable"),
    "eps": ("基本每股收益","每股收益","eps"), "roe": ("净资产收益率","roe","return on equity"),
    "roa": ("总资产收益率","roa","return on assets"), "gross_margin": ("毛利率","gross margin"),
    "net_margin": ("净利率","net margin"), "debt_ratio": ("资产负债率","debt ratio"),
    "current_ratio": ("流动比率","current ratio"), "segment_revenue": ("分部收入","分业务收入","segment revenue"),
}
FORMULAS = {"gross_margin": ("gross_profit","revenue"), "net_margin": ("net_profit","revenue"), "current_ratio": ("current_assets","current_liabilities"), "debt_ratio": ("total_liabilities","total_assets"), "cash_conversion": ("operating_cash_flow","net_profit"), "roe": ("net_profit","equity"), "roa": ("net_profit","total_assets"), "segment_contribution": ("segment_revenue","revenue")}
TASKS = (
    "image_caption","financial_ocr","entity_extraction_classification","spatial_localization","single_table_qa","multi_table_reasoning","chart_data_extraction","relationship_equity_structure","basic_arithmetic_metrics","statistics_comparison_ranking","candlestick_time_series","multi_step_numerical_reasoning","cross_modal_multi_hop","long_document_cross_page","evidence_retrieval","multimodal_financial_knowledge","explanation_anomaly_causality","financial_audit_fundamentals","industry_trend_inference","risk_sentiment_policy","investment_advice_strategy","portfolio_allocation_risk_return","summary_announcement","compliance_safety_suitability","financial_reconciliation","multi_visual_numerical_reasoning","multi_chart_reasoning","multi_table_chart_reasoning","multi_visual_retrieval","cross_document_financial_reasoning","fact_consistency_check"
)
NUMERIC_TASKS = {"basic_arithmetic_metrics","multi_step_numerical_reasoning","financial_reconciliation","multi_visual_numerical_reasoning"}
VISUAL_TASKS = {"image_caption","financial_ocr","spatial_localization","single_table_qa","multi_table_reasoning","chart_data_extraction","relationship_equity_structure","candlestick_time_series","cross_modal_multi_hop","multimodal_financial_knowledge","multi_visual_numerical_reasoning","multi_chart_reasoning","multi_table_chart_reasoning","multi_visual_retrieval"}

ENTITY_PROMPT = '''识别金融文档实体。输出JSON：{"company_name":"","ticker":"","market":"","industry_group":"","doc_type":"annual_report|semiannual_report|quarterly_report|esg_report|research_report|prospectus|announcement|other","period":"","frequency":"annual|semiannual|quarterly|unknown"}。只使用输入材料，规则hints明确的内容不得无依据改写。'''
FACT_PROMPT = '''你是金融事实标准化器。输入有document_entity、原文、rule_candidates和原始图片。输出{"facts":[{"candidate_id":"","metric":"","metric_canonical":"","value_text":"","numeric_value":"","unit":"","currency":"","period":"","scope":"","statement_type":"income_statement|balance_sheet|cash_flow|notes|chart|other","source_mode":"text|image","image_index":null,"visual_type":"table|chart|candlestick|relationship_diagram|terminal|document_page|other|none","visual_observation":"","evidence_quote":""}]}。文本数值fact必须引用rule_candidates.candidate_id且数字/metric_canonical保持一致；图片fact必须直接看图，精确数值看不清时只抽视觉关系；K线只描述历史可见信息；不得使用原QA答案。'''
RECHECK_PROMPT = '''复核一个低置信度金融fact。输出{"accepted":true,"reason":""}。只有原文或原图能直接支持metric/value/period/scope时accepted=true。'''
PLAN_PROMPT = '''基于真实金融facts规划可程序验证的数值题。输出{"status":"accepted|reject","evidence_ids":[],"steps":[{"id":"s1","operator":"ratio|difference|percentage_change|yoy_growth|gross_margin|net_margin|current_ratio|debt_ratio|cash_conversion|roe|roa|segment_contribution|component_sum","expression":"仅v0/v1/...、前序sN、+ - * /括号和常数1,2,4,12,100,360,365,10000,100000000","claimed_result":"数字","unit":"","evidence_ids":[]}],"answer_value":"","answer_unit":"","question":""}。至少使用2个真实facts；difficulty=easy 时允许1步，medium至少2步，hard至少3步并形成依赖链；主体/期间/scope/单位必须兼容；不得新增数字。'''
QA_PROMPT = '''根据requested_task和真实金融facts/原图生成训练QA。输出{"status":"accepted|reject","task_type":"","question":"","answer":"","answer_type":"short_text|free_text|number|page_numbers|image_indices","evidence_ids":[],"visual_evidence_ids":[],"reasoning":""}。公司名、日期、指标名保持明确；遵守输入 difficulty：easy可单证据，medium至少2条关键证据，hard至少3条关键证据并包含跨页/多表/多图/口径对齐中的至少一项；视觉任务必须直接看图且图片不可被文字替代；多表/多图至少两张图参与；K线不预测未来；开放分析不超出材料。'''
JUDGE_PROMPT = '''独立审核金融QA。输出{"supported":true,"answerable":true,"visual_required":true,"score":5,"reason":""}。答案必须被给定facts和原图支持；视觉任务必须真的需要图片；score<4代表应过滤。'''


def sid(prefix: str, *xs: Any) -> str:
    return prefix + "_" + hashlib.sha256("\0".join(map(str,xs)).encode()).hexdigest()[:16]

def write_jsonl(path: Path, rows: list[dict[str,Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows: f.write(json.dumps(row, ensure_ascii=False, separators=(",",":")) + "\n")

def read_jsonl(path: Path) -> list[dict[str,Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def clean_obj(x: Any) -> Any:
    if isinstance(x, dict): return {k: clean_obj(v) for k,v in x.items() if str(k).casefold() not in SUPERVISION and str(k).casefold() not in IMAGE_KEYS}
    if isinstance(x, list): return [clean_obj(v) for v in x]
    return x

def render(x: Any) -> str:
    if isinstance(x, str): return x
    if isinstance(x, (int,float)): return str(x)
    if isinstance(x, list): return "\n".join(filter(None,(render(v) for v in x)))
    if isinstance(x, dict): return "\n".join(f"{k}: {s}" for k,v in x.items() if (s:=render(v)))
    return ""

def context_text(row: Any) -> str:
    if not isinstance(row, dict): return render(row)
    parts=[]
    for k,v in row.items():
        if str(k).casefold() in CONTEXT: parts.append(render(v))
    text="\n".join(x for x in parts if x.strip())
    return text if text else render(clean_obj(row))

def iter_records(path: Path):
    s=path.suffix.lower()
    if s==".jsonl":
        for i,line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(),1):
            if line.strip(): yield i,json.loads(line)
    elif s==".json":
        x=json.loads(path.read_text(encoding="utf-8-sig")); seq=x if isinstance(x,list) else next((x[k] for k in ("data","items","records") if isinstance(x.get(k),list)),[x])
        for i,row in enumerate(seq,1): yield i,row
    elif s==".csv":
        with path.open(encoding="utf-8-sig",newline="") as f:
            for i,row in enumerate(csv.DictReader(f),1): yield i,row
    elif s==".parquet":
        import pyarrow.parquet as pq
        i=0
        for b in pq.ParquetFile(path).iter_batches(batch_size=128):
            for row in b.to_pylist(): i+=1; yield i,row
    else: yield 1,{"text":path.read_text(encoding="utf-8",errors="replace")}

def record_images(row: Any, source: Path, raw: Path, out: Path, key: str) -> list[str]:
    images=[]
    def visit(x):
        if isinstance(x, dict):
            data=x.get("bytes")
            if isinstance(data,(bytes,bytearray,memoryview)):
                target=out/"source_media"/(sid("img",source,key,len(images))+".png"); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(bytes(data)); images.append(target.relative_to(PROJECT_ROOT).as_posix())
            for k,v in x.items():
                if str(k).casefold() in IMAGE_KEYS: visit(v)
        elif isinstance(x,list):
            for v in x: visit(v)
        elif isinstance(x,str):
            candidate=Path(x); opts=[candidate] if candidate.is_absolute() else [source.parent/candidate,raw/candidate,PROJECT_ROOT/candidate]
            found=next((v for v in opts if v.is_file() and v.suffix.lower() in IMAGE_SUFFIXES),None)
            if found:
                rel=found.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
                if rel not in images: images.append(rel)
    if isinstance(row,dict):
        for k,v in row.items():
            if str(k).casefold() in IMAGE_KEYS: visit(v)
    return images[:5]

def extract_units(raw: Path, out: Path, dpi: int) -> list[dict[str,Any]]:
    units=[]
    for path in sorted(raw.rglob("*")):
        if not path.is_file(): continue
        rel=path.relative_to(PROJECT_ROOT).as_posix(); dataset=path.relative_to(raw).parts[0]
        if path.suffix.lower()==".pdf":
            import fitz
            doc=fitz.open(path); doc_id=sid("doc",rel)
            for n,page in enumerate(doc,1):
                d=out/"documents"/doc_id/"pages"/f"{n:04d}"; d.mkdir(parents=True,exist_ok=True)
                img=d/"page.png"; page.get_pixmap(matrix=fitz.Matrix(dpi/72,dpi/72),alpha=False).save(img)
                text=page.get_text("text").strip(); (d/"page.txt").write_text(text,encoding="utf-8")
                units.append({"unit_id":sid("u",rel,n),"dataset":dataset,"document_id":doc_id,"source_ref":f"{rel}#page={n}","page":n,"text":text[:20000],"images":[img.relative_to(PROJECT_ROOT).as_posix()]})
            doc.close(); continue
        if path.suffix.lower() in IMAGE_SUFFIXES:
            units.append({"unit_id":sid("u",rel),"dataset":dataset,"document_id":sid("doc",rel),"source_ref":rel,"page":None,"text":"","images":[rel]}); continue
        if path.suffix.lower() not in {".jsonl",".json",".csv",".parquet",".txt",".md"}: continue
        for i,row in iter_records(path):
            text=context_text(row).strip()
            if not text: continue
            units.append({"unit_id":sid("u",rel,i),"dataset":dataset,"document_id":sid("doc",rel,(row.get("document_id") if isinstance(row,dict) else "") or i),"source_ref":f"{rel}#{i}","page":row.get("page") if isinstance(row,dict) else None,"text":text[:20000],"images":record_images(row,path,raw,out,str(i))})
    write_jsonl(out/"evidence_units.jsonl",units); return units

class Qwen:
    def __init__(self, model: str, tp: int, max_len: int, max_images: int):
        from transformers import AutoProcessor
        from vllm import LLM, SamplingParams
        self.model=model; self.processor=AutoProcessor.from_pretrained(model,trust_remote_code=True); self.SamplingParams=SamplingParams
        self.llm=LLM(model=model,trust_remote_code=True,tensor_parallel_size=tp,max_model_len=max_len,limit_mm_per_prompt={"image":max_images})
    def json(self, system: str, payload: Any, images: list[str]=[], temp: float=.1, max_tokens: int=2048) -> dict[str,Any]:
        from qwen_vl_utils import process_vision_info
        content=[{"type":"text","text":payload if isinstance(payload,str) else json.dumps(payload,ensure_ascii=False)}]
        for image in images: content.append({"type":"image","image":(PROJECT_ROOT/image).resolve().as_uri()})
        msgs=[{"role":"system","content":[{"type":"text","text":system}]},{"role":"user","content":content}]
        prompt=self.processor.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True); imgs,_=process_vision_info(msgs); req={"prompt":prompt}
        if imgs: req["multi_modal_data"]={"image":imgs}
        out=self.llm.generate([req],self.SamplingParams(temperature=temp,top_p=.9,max_tokens=max_tokens),use_tqdm=False)[0].outputs[0].text
        a,b=out.find("{"),out.rfind("}")
        if a<0 or b<a: raise ValueError("no JSON")
        return json.loads(out[a:b+1])

def entity_hint(text: str, ref: str) -> dict[str,str]:
    t=TICKER_RE.search(ref+"\n"+text); years=YEAR_RE.findall(ref+"\n"+text); c=COMPANY_RE.search(text[:10000]); low=(ref+text).lower()
    dtype="annual_report" if "年度报告" in low or "annual report" in low else "semiannual_report" if "半年度" in low else "quarterly_report" if "季度" in low else "research_report" if "研报" in low or "research report" in low else "other"
    ticker=t.group(1) if t else ""; market="SSE" if ticker.startswith("6") else "SZSE" if ticker.startswith(("0","3")) else "BSE" if ticker.startswith(("4","8","9")) else "unknown"
    return {"company_name":c.group(1) if c else "","ticker":ticker,"market":market,"period":max(years) if years else "","doc_type":dtype}

def build_entities(q: Qwen, units: list[dict[str,Any]], out: Path) -> list[dict[str,Any]]:
    by=defaultdict(list)
    for u in units: by[u["document_id"]].append(u)
    rows=[]
    for doc_id,us in by.items():
        text="\n".join(u["text"] for u in us[:5])[:15000]; hint=entity_hint(text,us[0]["source_ref"]); images=us[0].get("images",[])[:1]
        try: m=q.json(ENTITY_PROMPT,{"hints":hint,"text":text},images)
        except Exception: m={}
        e={"document_id":doc_id,"company_name":hint["company_name"] or m.get("company_name",""),"ticker":hint["ticker"] or m.get("ticker",""),"market":hint["market"] if hint["market"]!="unknown" else m.get("market","unknown"),"industry_group":m.get("industry_group",""),"doc_type":hint["doc_type"] if hint["doc_type"]!="other" else m.get("doc_type","other"),"period":hint["period"] or m.get("period",""),"frequency":m.get("frequency","unknown")}
        e["entity_id"]=sid("company",e["ticker"] or e["company_name"] or doc_id); rows.append(e)
    write_jsonl(out/"document_entities.jsonl",rows); companies={}
    for e in rows: companies.setdefault(e["entity_id"],{k:e.get(k,"") for k in ("entity_id","company_name","ticker","market","industry_group")})
    write_jsonl(out/"company_entities.jsonl",list(companies.values())); return rows

def metric_hits(text: str):
    hits=[]
    low=text.casefold()
    for canon,aliases in METRICS.items():
        for alias in sorted(aliases,key=len,reverse=True):
            start=low.find(alias.casefold())
            if start>=0: hits.append((start,start+len(alias),canon,text[start:start+len(alias)])); break
    return sorted(hits)

def candidates(unit: dict[str,Any], ent: dict[str,Any]) -> list[dict[str,Any]]:
    rows=[]
    for sent in re.split(r"(?<=[。！？!?;；])|\n+",unit["text"]):
        ms=metric_hits(sent); vs=list(VALUE_RE.finditer(sent))
        for start,end,canon,label in ms:
            after=[v for v in vs if v.start()>=end]; v=min(after,key=lambda x:x.start()-end) if after else min(vs,key=lambda x:abs(x.start()-end),default=None)
            if not v or abs(v.start()-end)>100: continue
            raw=v.group(0).strip(); num=NUM_RE.search(raw)
            if not num: continue
            value=num.group(0).replace(",",""); unit_text=raw[num.end():].strip(); period=(YEAR_RE.search(sent).group(1) if YEAR_RE.search(sent) else ent.get("period",""))
            rows.append({"candidate_id":sid("c",unit["unit_id"],canon,value,start),"unit_id":unit["unit_id"],"metric":label,"metric_canonical":canon,"numeric_value":value,"value_text":raw,"unit":unit_text,"period":period,"scope":"","evidence_quote":sent.strip()[:500],"alignment_distance":abs(v.start()-end)})
    return rows

def build_facts(q: Qwen, units: list[dict[str,Any]], entities: list[dict[str,Any]], out: Path, trusted=.9, recheck=.75):
    em={e["document_id"]:e for e in entities}; allc=[]; facts=[]; quarantine=[]
    for u in units:
        ent=em[u["document_id"]]; cs=candidates(u,ent); allc.extend(cs); cmap={c["candidate_id"]:c for c in cs}
        try: result=q.json(FACT_PROMPT,{"document_entity":ent,"text":u["text"],"rule_candidates":cs},u.get("images",[])[:5],max_tokens=4096)
        except Exception: result={"facts":[]}
        for raw in result.get("facts",[]):
            cid=raw.get("candidate_id",""); mode=raw.get("source_mode","text")
            if mode=="text" and raw.get("numeric_value") and cid not in cmap: continue
            base=cmap.get(cid,{})
            f={"fact_id":sid("f",u["unit_id"],cid or len(facts),raw.get("metric"),raw.get("evidence_quote")),"document_id":u["document_id"],"entity_id":ent["entity_id"],"company_name":ent.get("company_name",""),"industry_group":ent.get("industry_group",""),"source_ref":u["source_ref"],"page":u.get("page"),"metric":base.get("metric") or raw.get("metric",""),"metric_canonical":base.get("metric_canonical") or raw.get("metric_canonical",""),"value_text":base.get("value_text") or raw.get("value_text",""),"numeric_value":base.get("numeric_value") or raw.get("numeric_value",""),"unit":base.get("unit") or raw.get("unit",""),"currency":raw.get("currency",""),"period":base.get("period") or raw.get("period") or ent.get("period",""),"scope":raw.get("scope",""),"statement_type":raw.get("statement_type","other"),"source_mode":mode,"image_index":raw.get("image_index"),"visual_type":raw.get("visual_type","none"),"visual_observation":raw.get("visual_observation",""),"evidence_quote":base.get("evidence_quote") or raw.get("evidence_quote",""),"images":u.get("images",[])}
            f["extractor_model"]=q.model; score=.35 if cid else .1; score+=.25 if f["numeric_value"] else .1; score+=.15 if f["period"] else 0; score+=.1 if f["metric_canonical"] else 0; score+=.1 if mode=="image" and f["images"] else 0; score+=.05 if f["scope"] else 0; f["confidence"]=round(min(score,1),3)
            if f["confidence"]>=trusted: facts.append(f)
            elif f["confidence"]>=recheck:
                try: chk=q.json(RECHECK_PROMPT,{"fact":f,"text":u["text"],"rule_candidates":cs},u.get("images",[])[:5])
                except Exception: chk={"accepted":False}
                (facts if chk.get("accepted") else quarantine).append(f)
            else: quarantine.append(f)
    write_jsonl(out/"fact_candidates.jsonl",allc); write_jsonl(out/"graph_facts.jsonl",facts); write_jsonl(out/"fact_quarantine.jsonl",quarantine); return facts

def build_graph(facts: list[dict[str,Any]], entities: list[dict[str,Any]], out: Path) -> list[dict[str,Any]]:
    edges={}; groups=defaultdict(list)
    for f in facts:
        for typ,key in (("same_company_metric",f'{f["entity_id"]}|{f["metric_canonical"]}'),("same_company_period",f'{f["entity_id"]}|{f["period"]}'),("same_metric_period",f'{f["metric_canonical"]}|{f["period"]}'),("same_source",f["source_ref"])):
            if key.strip("|"): groups[(typ,key)].append(f["fact_id"])
    for (typ,_),ids in groups.items():
        for a,b in zip(ids,ids[1:]): edges[(a,b,typ)]={"a":a,"b":b,"type":typ}
    buckets=defaultdict(dict)
    for f in facts:
        buckets[(f["entity_id"],f["period"],f["scope"],f["unit"])][f["metric_canonical"]]=f
    for _,by in buckets.items():
        for formula,metrics in FORMULAS.items():
            if all(m in by for m in metrics):
                ids=[by[m]["fact_id"] for m in metrics]
                for a,b in zip(ids,ids[1:]): edges[(a,b,"financial_formula:"+formula)]={"a":a,"b":b,"type":"financial_formula:"+formula}
    rows=list(edges.values()); write_jsonl(out/"graph_edges.jsonl",rows)
    ent_edges=[]
    for i,a in enumerate(entities):
        for b in entities[i+1:]:
            typ="same_company_cross_period" if a["entity_id"]==b["entity_id"] and a.get("period")!=b.get("period") else "same_industry_peer" if a.get("industry_group") and a.get("industry_group")==b.get("industry_group") and a["entity_id"]!=b["entity_id"] else ""
            if typ: ent_edges.append({"a":a["document_id"],"b":b["document_id"],"type":typ})
    write_jsonl(out/"entity_edges.jsonl",ent_edges); return rows

def adjacency(edges):
    g=defaultdict(list)
    for e in edges: g[e["a"]].append(e["b"]); g[e["b"]].append(e["a"])
    return g

def sample_facts(rng: random.Random, facts: list[dict[str,Any]], edges, task: str, n=10):
    if not facts: return []
    fmap={f["fact_id"]:f for f in facts}; g=adjacency(edges); seeds=[f for f in facts if (f["source_mode"]=="image")== (task in VISUAL_TASKS)] or facts
    cur=rng.choice(seeds)["fact_id"]; ids=[cur]
    while len(ids)<n:
        opts=[x for x in g.get(cur,[]) if x not in ids]
        if not opts: break
        cur=rng.choice(opts); ids.append(cur)
    return [fmap[x] for x in ids]

def eval_expr(expr: str, vals: dict[str,Decimal]) -> Decimal:
    tree=ast.parse(expr,mode="eval")
    def ev(n):
        if isinstance(n,ast.Expression): return ev(n.body)
        if isinstance(n,ast.Name) and n.id in vals: return vals[n.id]
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)): return Decimal(str(n.value))
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            a,b=ev(n.left),ev(n.right); return a+b if isinstance(n.op,ast.Add) else a-b if isinstance(n.op,ast.Sub) else a*b if isinstance(n.op,ast.Mult) else a/b
        raise ValueError(expr)
    return ev(tree)

def numeric_sample(q: Qwen, task: str, fs: list[dict[str,Any]], images: list[str], difficulty: str):
    nums=[f for f in fs if f.get("numeric_value")]
    if len(nums)<2: return None
    aliases={f"v{i}":f for i,f in enumerate(nums)}; payload={"task":task,"difficulty":difficulty,"facts":[{**f,"variable":v,"images":[]} for v,f in aliases.items()]}
    try: p=q.json(PLAN_PROMPT,payload,images,temp=.3,max_tokens=3072)
    except Exception: return None
    if p.get("status")!="accepted" or not p.get("question") or not p.get("steps"): return None
    vals={v:Decimal(f["numeric_value"].replace(",","")) for v,f in aliases.items()}; used=set()
    try:
        for i,s in enumerate(p["steps"],1):
            names={x.id for x in ast.walk(ast.parse(s["expression"],mode="eval")) if isinstance(x,ast.Name)}
            if i>1 and not any(n.startswith("s") for n in names): return None
            used|={n for n in names if n.startswith("v")}; vals[f"s{i}"]=eval_expr(s["expression"],vals)
            if abs(vals[f"s{i}"]-Decimal(str(s["claimed_result"])))>Decimal("0.0001"): return None
        ans=vals[f"s{len(p['steps'])}"]
        if abs(ans-Decimal(str(p["answer_value"])))>Decimal("0.0001"): return None
    except (ValueError,InvalidOperation,ZeroDivisionError): return None
    usedfacts=[aliases[x] for x in used if x in aliases]; return p,usedfacts

def synthesize(q: Qwen, facts, edges, out: Path, tasks: list[str], target: int, seed: int, easy_ratio: float, medium_ratio: float, hard_ratio: float):
    rng=random.Random(seed); sft=[]; rejected=[]; counts=Counter()
    normal=[t for t in tasks if t!="fact_consistency_check"]
    total_ratio=max(easy_ratio+medium_ratio+hard_ratio,1e-9); easy_cut=easy_ratio/total_ratio; medium_cut=(easy_ratio+medium_ratio)/total_ratio
    for attempt in range(target*30):
        if len(sft)>=target: break
        task=normal[attempt%len(normal)]; draw=rng.random(); difficulty="easy" if draw<easy_cut else "medium" if draw<medium_cut else "hard"; n_facts=4 if difficulty=="easy" else 7 if difficulty=="medium" else 10; fs=sample_facts(rng,facts,edges,task,n=n_facts); images=[]
        for f in fs:
            if f.get("source_mode")=="image":
                idx=f.get("image_index"); arr=f.get("images",[]); im=arr[idx] if isinstance(idx,int) and idx<len(arr) else arr[0] if len(arr)==1 else None
                if im and im not in images: images.append(im)
        images=images[:5]
        if task in NUMERIC_TASKS:
            result=numeric_sample(q,task,fs,images if task=="multi_visual_numerical_reasoning" else [],difficulty)
            if not result: continue
            p,used=result; question=p["question"]; answer=f'{p["answer_value"]}{p.get("answer_unit","")}'
        else:
            payload={"requested_task":task,"difficulty":difficulty,"facts":[{**f,"images":[]} for f in fs]}
            try: c=q.json(QA_PROMPT,payload,images,temp=.5,max_tokens=3072)
            except Exception: continue
            if c.get("status")!="accepted" or c.get("task_type")!=task: continue
            try: j=q.json(JUDGE_PROMPT,{"task":task,"question":c.get("question"),"answer":c.get("answer"),"facts":payload["facts"]},images,max_tokens=1024)
            except Exception: continue
            if not j.get("supported") or not j.get("answerable") or int(j.get("score",0))<4 or (task in VISUAL_TASKS and not j.get("visual_required")): continue
            question,answer=c["question"],c["answer"]; used=[f for f in fs if f["fact_id"] in set(c.get("evidence_ids",[]))] or fs[:2]
        prompt=("<image>"*len(images))+"参考材料：\n"+"\n".join(f'[{i+1}] {f["evidence_quote"]}' if f.get("source_mode")=="text" else f'[{i+1}] 请查看对应图片证据。' for i,f in enumerate(fs))+"\n\n问题："+question
        required_ids=[f["fact_id"] for f in used]
        distractor_ids=[f["fact_id"] for f in fs if f["fact_id"] not in set(required_ids)]
        if difficulty=="hard" and (len(required_ids)<3 or (task in NUMERIC_TASKS and len(p.get("steps",[]))<3)): continue
        if difficulty=="medium" and (len(required_ids)<2 or (task in NUMERIC_TASKS and len(p.get("steps",[]))<2)): continue
        row={"messages":[{"role":"user","content":prompt},{"role":"assistant","content":str(answer)}],"source":"finance_world_initial","split":"train","images":images,"task":task,"metadata":{"construction_type":task,"difficulty":{"label":difficulty,"required_fact_count":len(required_ids),"distractor_count":len(distractor_ids),"visual_fact_count":sum(f.get("source_mode")=="image" for f in used)},"required_evidence_ids":required_ids,"distractor_ids":distractor_ids,"evidence_ids":required_ids,"initial_synthesis":True,"extractor_model":next((f.get("extractor_model") for f in used if f.get("extractor_model")),EXTRACT_MODEL),"constructor_model":q.model}}
        sft.append(row); counts[task]+=1
    write_jsonl(out/"train_sft.jsonl",sft); (out/"train_rl_reasoning.jsonl").unlink(missing_ok=True); write_jsonl(out/"rejected.jsonl",rejected); (out/"audit.json").write_text(json.dumps({"accepted":len(sft),"tasks":counts,"note":"RL data is constructed by dedicated RL builders; this script emits SFT only."},ensure_ascii=False,indent=2),encoding="utf-8")

def consistency_negatives(cands, limit):
    by=defaultdict(list)
    for c in cands: by[c["unit_id"]].append(c)
    rows=[]
    for group in by.values():
        if len(group)<2: continue
        a,b=group[0],group[1]
        if a["numeric_value"]==b["numeric_value"]: continue
        q=f'材料是否支持“{a["metric"]}为{b["value_text"]}”这一陈述？'; ans=f'不支持。材料中{a["metric"]}为{a["value_text"]}，{b["value_text"]}对应{b["metric"]}。'
        rows.append({"messages":[{"role":"user","content":a["evidence_quote"]+"\n\n"+q},{"role":"assistant","content":ans}],"source":"finance_world_initial","split":"train","images":[],"task":"fact_consistency_check"})
        if len(rows)>=limit: break
    return rows

def parse_args():
    p=argparse.ArgumentParser()
    p.add_argument("--stage",choices=("extract","entities","facts","evidence","graph","synthesize","all"),default="all")
    p.add_argument("--raw-root",type=Path,default=RAW_ROOT)
    p.add_argument("--output-root",type=Path,default=OUT_ROOT)
    p.add_argument("--extract-model",default=EXTRACT_MODEL,help="32B model used only for entity/fact extraction")
    p.add_argument("--construct-model",default=CONSTRUCT_MODEL,help="235B model used for SFT construction")
    p.add_argument("--model",default="",help="Backward-compatible alias for --construct-model")
    p.add_argument("--tensor-parallel-size",type=int,default=8)
    p.add_argument("--max-model-len",type=int,default=32768)
    p.add_argument("--max-images",type=int,default=5)
    p.add_argument("--pdf-dpi",type=int,default=144)
    p.add_argument("--target",type=int,default=2000)
    p.add_argument("--tasks",nargs="+",choices=TASKS,default=list(TASKS))
    p.add_argument("--seed",type=int,default=42)
    p.add_argument("--easy-ratio",type=float,default=.35)
    p.add_argument("--medium-ratio",type=float,default=.45)
    p.add_argument("--hard-ratio",type=float,default=.20)
    p.add_argument("--consistency-negative-ratio",type=float,default=.05)
    a=p.parse_args()
    if a.model:
        a.construct_model=a.model
    return a

def _run_all_children():
    raw=sys.argv[1:]; rest=[]; skip=False
    for token in raw:
        if skip:
            skip=False; continue
        if token=="--stage":
            skip=True; continue
        if token.startswith("--stage="):
            continue
        rest.append(token)
    for stage in ("extract","evidence","graph","synthesize"):
        cmd=[sys.executable,str(Path(__file__).resolve()),"--stage",stage,*rest]
        print("+"," ".join(cmd),flush=True)
        rc=subprocess.run(cmd).returncode
        if rc:
            raise SystemExit(rc)

def main():
    a=parse_args(); a.output_root.mkdir(parents=True,exist_ok=True)
    if a.stage=="all":
        _run_all_children(); return
    units_path=a.output_root/"evidence_units.jsonl"; ents_path=a.output_root/"document_entities.jsonl"; facts_path=a.output_root/"graph_facts.jsonl"; edges_path=a.output_root/"graph_edges.jsonl"
    if a.stage=="extract":
        extract_units(a.raw_root,a.output_root,a.pdf_dpi); return
    if a.stage in {"entities","facts","evidence"}:
        q=Qwen(a.extract_model,a.tensor_parallel_size,a.max_model_len,a.max_images)
        if a.stage in {"entities","evidence"}:
            build_entities(q,read_jsonl(units_path),a.output_root)
        if a.stage in {"facts","evidence"}:
            build_facts(q,read_jsonl(units_path),read_jsonl(ents_path),a.output_root)
        return
    if a.stage=="graph":
        build_graph(read_jsonl(facts_path),read_jsonl(ents_path),a.output_root); return
    if a.stage=="synthesize":
        q=Qwen(a.construct_model,a.tensor_parallel_size,a.max_model_len,a.max_images)
        synthesize(q,read_jsonl(facts_path),read_jsonl(edges_path),a.output_root,a.tasks,a.target,a.seed,a.easy_ratio,a.medium_ratio,a.hard_ratio)
        if "fact_consistency_check" in a.tasks:
            rows=read_jsonl(a.output_root/"train_sft.jsonl"); neg=consistency_negatives(read_jsonl(a.output_root/"fact_candidates.jsonl"),max(1,int(a.target*a.consistency_negative_ratio))); write_jsonl(a.output_root/"train_sft.jsonl",rows+neg)

if __name__=="__main__": main()
