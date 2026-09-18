#!/usr/bin/env python3
"""Bad-case driven finance data flywheel for FINAR-VL.

Known bad cases under data/error are sent to Qwen235 only for taxonomy
classification. New training data is synthesized from trusted finance-world
facts/edges, with task/error/scenario-aware visual constraints and hierarchical
evidence retrieval:
  same document -> same entity+period -> adjacent period -> other period ->
  industry peer only when cross-company reasoning is explicitly intended.
"""
from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import io
import json
import os
import random
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ERROR_ROOT = PROJECT_ROOT / "data" / "error"
DEFAULT_WORLD = PROJECT_ROOT / "data" / "synthetic" / "finance_world"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "synthetic" / "badcase_flywheel"
DEFAULT_MODEL = PROJECT_ROOT / "model" / "qwen235"

TASK_TYPES = (
    "image_caption","financial_ocr","entity_extraction_classification","spatial_localization",
    "single_table_qa","multi_table_reasoning","chart_data_extraction","relationship_equity_structure",
    "basic_arithmetic_metrics","statistics_comparison_ranking","candlestick_time_series",
    "multi_step_numerical_reasoning","cross_modal_multi_hop","long_document_cross_page",
    "evidence_retrieval","multimodal_financial_knowledge","explanation_anomaly_causality",
    "financial_audit_fundamentals","industry_trend_inference","risk_sentiment_policy",
    "investment_advice_strategy","portfolio_allocation_risk_return","summary_announcement",
    "compliance_safety_suitability","financial_reconciliation","multi_visual_numerical_reasoning",
    "multi_chart_reasoning","multi_table_chart_reasoning","multi_visual_retrieval","fact_consistency_check",
)
NUMERIC_TASKS = {"basic_arithmetic_metrics","multi_step_numerical_reasoning","financial_reconciliation","multi_visual_numerical_reasoning"}

ERROR_TYPES = {
    "visual_ocr_text_error":"图片文字/标签/实体名/指标名读取错误",
    "visual_ocr_number_error":"图片数字、小数点、正负号、百分号或单位读取错误",
    "layout_spatial_error":"页面版面、区域、标题归属或空间关系错误",
    "table_header_error":"表头、多级表头、年份列或单位栏理解错误",
    "table_row_column_alignment_error":"表格行列、字段和值对应错误",
    "table_merged_cell_error":"合并单元格、跨栏或层级表结构错误",
    "chart_axis_error":"图表轴、刻度、单位或时间轴理解错误",
    "chart_legend_series_error":"图例和数据系列对应错误",
    "chart_value_reading_error":"图表数值读取错误",
    "chart_trend_error":"图表趋势、拐点、峰谷或方向判断错误",
    "candlestick_ohlc_error":"K线开高低收或阳阴线识别错误",
    "candlestick_trend_error":"K线历史区间趋势、峰谷或连续涨跌理解错误",
    "relationship_diagram_error":"股权/控股/组织/交易关系图理解错误",
    "single_evidence_retrieval_error":"未定位到关键证据",
    "cross_page_retrieval_error":"跨页漏页、选错页或页面组合错误",
    "multi_document_retrieval_error":"多文档找错文档或遗漏文档",
    "evidence_coverage_error":"只找到部分必要证据",
    "evidence_relevance_error":"使用相关但不支持答案的证据",
    "visual_retrieval_error":"多图中选错表/图/K线/页面",
    "entity_confusion_error":"公司、证券、业务、分部、人员或产品实体混淆",
    "period_confusion_error":"年份、季度、半年、期初期末或同比基期选择错误",
    "scope_confusion_error":"合并、母公司、分部、地区、产品等口径混淆",
    "metric_confusion_error":"相近金融指标选择错误",
    "statement_line_item_error":"财报或附注科目选择错误",
    "segment_confusion_error":"业务分部、地区、产品或客户类别选错",
    "unit_scale_error":"元/万元/亿元、千/百万/十亿、百分比/小数等量级错误",
    "currency_error":"币种识别或换算错误","sign_direction_error":"正负、流入流出或增减方向错误",
    "baseline_reference_error":"同比/环比基期或比较基准选择错误",
    "cross_modal_alignment_error":"文本与表格/图表/图片同一事实未正确对齐",
    "multi_table_alignment_error":"多表实体、字段、期间、单位或口径对齐错误",
    "multi_chart_alignment_error":"多图系列、指标、期间或实体对齐错误",
    "entity_extraction_error":"金融实体抽取错误","attribute_extraction_error":"实体属性/数值/日期/事件属性抽取错误",
    "entity_disambiguation_error":"同名或近名实体消歧错误","financial_classification_error":"金融文本/事件类别判断错误",
    "choice_mapping_error":"语义答案到选项映射错误","fact_verification_error":"材料是否支持事实的判断错误",
    "financial_knowledge_error":"金融概念、指标定义或报表含义知识错误",
    "accounting_semantics_error":"会计科目、口径或报表语义错误","instrument_knowledge_error":"金融工具知识错误",
    "formula_selection_error":"金融公式或计算关系选择错误","arithmetic_error":"纯数值计算执行错误",
    "ratio_percentage_error":"比率、百分比、增长率或占比计算错误","aggregation_error":"求和、平均、加权或合计错误",
    "reconciliation_error":"报表勾稽、期初期末、分部到合并或组成项到总额错误",
    "multi_step_reasoning_error":"多步依赖或中间结果组合错误","comparison_error":"比较、差值或方向判断错误",
    "ranking_error":"排序、最大最小判断错误","temporal_reasoning_error":"跨期趋势、同比/环比推理错误",
    "conditional_logic_error":"多条件、阈值或筛选逻辑错误",
    "explanation_error":"材料解释理解错误","causal_attribution_error":"因果归因错误",
    "anomaly_interpretation_error":"异常值或突变解释错误","fundamental_analysis_error":"基本面分析错误",
    "audit_reasoning_error":"审计、勾稽、一致性或异常核验错误","industry_trend_error":"行业趋势或结构判断错误",
    "company_comparison_error":"跨公司基本面或指标比较错误","risk_identification_error":"风险识别或分类错误",
    "risk_severity_error":"风险严重度、范围或优先级错误","sentiment_error":"金融文本情感/倾向判断错误",
    "policy_interpretation_error":"政策内容或方向理解错误","policy_impact_error":"政策影响的材料内推断错误",
    "regulatory_interpretation_error":"监管要求或披露语义错误","compliance_judgment_error":"合规或披露判断错误",
    "suitability_error":"适当性、风险承受与产品匹配错误","strategy_evaluation_error":"给定投资/交易策略评价错误",
    "portfolio_allocation_error":"资产配置、权重或组合结构错误","portfolio_risk_return_error":"组合风险收益、贡献或分散化错误",
    "summary_keypoint_omission_error":"摘要遗漏关键事实/数字/风险/事件","summary_fact_distortion_error":"摘要歪曲事实/数字/主体/期间/方向",
    "announcement_interpretation_error":"公告核心事项、条件、时间或影响解读错误",
    "unsupported_inference_error":"引入材料外事实或结论","insufficient_evidence_handling_error":"材料不足仍强行回答",
    "over_refusal_error":"材料足够却错误拒答","instruction_following_error":"未遵守输出内容或约束",
    "answer_format_error":"数字、单位、页码、JSON或选项格式错误","answer_granularity_error":"答案粒度错误","other_error":"其他错误",
}
SCENARIO_TAGS = {
    "annual_report":"年报","quarterly_report":"季报","semiannual_report":"半年报","earnings_release":"业绩快报/预告",
    "company_announcement":"公司公告","prospectus":"招股书/募集说明书","research_report":"研报","industry_report":"行业报告",
    "fund_report":"基金报告","regulatory_document":"监管文件","policy_document":"政策文件","financial_news":"金融新闻",
    "market_terminal":"行情终端","income_statement":"利润表","balance_sheet":"资产负债表","cash_flow_statement":"现金流量表",
    "financial_notes":"财报附注","segment_reporting":"分部披露","ownership_structure":"股权/组织关系","corporate_action":"公司行动",
    "earnings_analysis":"业绩分析","cashflow_analysis":"现金流分析","solvency_analysis":"偿债分析","valuation_analysis":"估值分析",
    "stock_market":"股票市场","candlestick_chart":"K线","technical_chart":"技术图表","fund":"基金","portfolio":"组合",
    "fixed_income":"固收","derivatives":"衍生品","banking":"银行","insurance":"保险","securities":"证券",
    "company_fundamentals":"公司基本面","peer_comparison":"同行比较","industry_analysis":"行业分析","risk_analysis":"风险分析",
    "sentiment_analysis":"情感分析","policy_analysis":"政策分析","compliance":"合规/适当性","investment_strategy":"投资策略",
    "plain_text":"纯文本","single_table":"单表","multi_table":"多表","single_chart":"单图","multi_chart":"多图",
    "table_chart_mixed":"表+图","text_table_mixed":"文本+表","text_chart_mixed":"文本+图","cross_modal":"跨模态",
    "single_page":"单页","cross_page":"跨页","multi_document":"多文档","long_document":"长文档","relationship_diagram":"关系图",
}
VISUAL_ERRORS = {e for e in ERROR_TYPES if e.startswith(("visual_","table_","chart_","candlestick_"))} | {
    "layout_spatial_error","relationship_diagram_error","visual_retrieval_error","cross_modal_alignment_error","multi_table_alignment_error","multi_chart_alignment_error"
}
CONFUSION_ERRORS = {"entity_confusion_error","period_confusion_error","scope_confusion_error","metric_confusion_error","statement_line_item_error","segment_confusion_error","unit_scale_error","currency_error","baseline_reference_error"}

TASK_VISUAL = {
    "image_caption":{"min_images":1},"financial_ocr":{"min_images":1},"spatial_localization":{"min_images":1},
    "single_table_qa":{"min_images":1,"families":[["table"]]},"multi_table_reasoning":{"min_images":2,"families":[["table"]]},
    "chart_data_extraction":{"min_images":1,"families":[["chart","candlestick"]]},
    "relationship_equity_structure":{"min_images":1,"families":[["relationship"]]},
    "candlestick_time_series":{"min_images":1,"families":[["candlestick"]]},
    "cross_modal_multi_hop":{"min_images":1,"min_text":1},"multimodal_financial_knowledge":{"min_images":1},
    "multi_visual_numerical_reasoning":{"min_images":2,"visual_numeric":True},
    "multi_chart_reasoning":{"min_images":2,"families":[["chart","candlestick"]]},
    "multi_table_chart_reasoning":{"min_images":2,"families":[["table"],["chart","candlestick"]]},
    "multi_visual_retrieval":{"min_images":2},
}
SCENARIO_VISUAL = {
    "single_table":{"min_images":1,"families":[["table"]]},"multi_table":{"min_images":2,"families":[["table"]]},
    "single_chart":{"min_images":1,"families":[["chart","candlestick"]]},"multi_chart":{"min_images":2,"families":[["chart","candlestick"]]},
    "table_chart_mixed":{"min_images":2,"families":[["table"],["chart","candlestick"]]},
    "text_table_mixed":{"min_images":1,"min_text":1,"families":[["table"]]},
    "text_chart_mixed":{"min_images":1,"min_text":1,"families":[["chart","candlestick"]]},
    "cross_modal":{"min_images":1,"min_text":1},"candlestick_chart":{"min_images":1,"families":[["candlestick"]]},
    "relationship_diagram":{"min_images":1,"families":[["relationship"]]},"cross_page":{"min_pages":2},"long_document":{"min_pages":2},
}
CROSS_COMPANY_TASKS = {"statistics_comparison_ranking","industry_trend_inference"}
CROSS_COMPANY_ERRORS = {"company_comparison_error","industry_trend_error"}
CROSS_COMPANY_SCENARIOS = {"peer_comparison","industry_analysis"}

CLASSIFY_SYSTEM = """你是金融模型bad case分类器。输入已确定是bad case，不要判断它是否真的错，不要重新验证gold，也不要创造新类别。只从提供的task_types/error_types/scenario_tags中选择。输出JSON：{\"task_type\":\"...\",\"error_type\":\"...\",\"scenario_tags\":[\"...\"],\"reason\":\"一句话\",\"focus\":[\"后续造数据重点\"]}。只选一个主要error_type；非计算题也必须分类。"""
SYNTH_SYSTEM = """你是金融bad-case定向数据构造器。输入包含原bad case分类、新的真实facts/edges、visual_policy和generation_rule。生成内容不同但训练同一错误能力的新样本。严格输出JSON：{\"status\":\"accepted|reject\",\"task_type\":\"...\",\"question\":\"...\",\"answer\":\"...\",\"answer_type\":\"short_text|free_text|number|choice|page_numbers|image_indices|json\",\"evidence_ids\":[\"fact_id\"],\"hard_negative_ids\":[\"fact_id\"],\"visual_evidence_ids\":[\"fact_id\"],\"reasoning_steps\":[\"...\"],\"program\":[{\"expression\":\"v0/v1等\",\"claimed_result\":\"数字\",\"unit\":\"单位\"}],\"generation_tags\":[\"...\"]}。所有事实/数字必须来自facts；confusion类必须有真实干扰；required视觉策略必须满足；K线不预测未来；跨公司仅在输入明确允许时使用；无法自然构造就reject。"""
VERIFY_SYSTEM = """你是金融合成数据审核器，只审核新样本。检查真实facts/图片是否支持、是否训练指定error_type、是否满足visual_policy、是否明显不同于原bad case。输出JSON：{\"supported\":true,\"targets_failure\":true,\"answerable\":true,\"visual_required\":false,\"novel\":true,\"score\":5,\"reason\":\"...\"}。"""


def parse_args():
    p=argparse.ArgumentParser(description="Bad-case driven finance data flywheel")
    p.add_argument("--error-root",type=Path,default=DEFAULT_ERROR_ROOT); p.add_argument("--facts",type=Path,default=DEFAULT_WORLD/"graph_facts.jsonl"); p.add_argument("--edges",type=Path,default=DEFAULT_WORLD/"graph_edges.jsonl")
    p.add_argument("--output-root",type=Path,default=DEFAULT_OUTPUT); p.add_argument("--model",type=Path,default=DEFAULT_MODEL); p.add_argument("--backend",choices=("vllm","openai"),default="vllm")
    p.add_argument("--base-url",default=os.getenv("FINAR_SYNTH_BASE_URL","http://127.0.0.1:8000/v1")); p.add_argument("--api-key",default=os.getenv("FINAR_SYNTH_API_KEY","EMPTY"))
    p.add_argument("--tensor-parallel-size",type=int,default=8); p.add_argument("--gpu-memory-utilization",type=float,default=.9)
    p.add_argument("--variants-per-case",type=int,default=6); p.add_argument("--attempt-multiplier",type=int,default=5); p.add_argument("--max-facts",type=int,default=12); p.add_argument("--max-cases",type=int,default=0)
    p.add_argument("--min-judge-score",type=int,default=4); p.add_argument("--cross-scenario-ratio",type=float,default=.25); p.add_argument("--prefer-visual-ratio",type=float,default=.8); p.add_argument("--seed",type=int,default=42)
    return p.parse_args()

def read_jsonl(path):
    with path.open(encoding="utf-8-sig") as f: return [json.loads(x) for x in f if x.strip()]
def write_jsonl(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="\n") as f:
        for row in rows: f.write(json.dumps(row,ensure_ascii=False,separators=(",",":"))+"\n")
def sid(prefix,*parts): return f"{prefix}_{hashlib.sha256(chr(0).join(map(str,parts)).encode()).hexdigest()[:16]}"
def iter_errors(root):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".json",".jsonl"}: continue
        if path.suffix.lower()==".jsonl":
            with path.open(encoding="utf-8-sig") as f: rows=[json.loads(x) for x in f if x.strip()]
        else:
            obj=json.loads(path.read_text(encoding="utf-8-sig")); rows=obj if isinstance(obj,list) else next((obj[k] for k in ("data","items","records","errors","bad_cases") if isinstance(obj.get(k),list)),[obj])
        for i,row in enumerate(rows,1):
            if isinstance(row,dict): yield path.relative_to(root).as_posix(),i,row
def normalize_bad(source,line,row):
    q=row.get("question")
    if q is None:
        for m in row.get("messages") or []:
            if isinstance(m,dict) and m.get("role")=="user": q=m.get("content"); break
    return {"badcase_id":str(row.get("badcase_id") or row.get("sample_id") or row.get("id") or sid("bad",source,line)),"source_file":source,"task":str(row.get("task") or row.get("task_type") or (row.get("metadata") or {}).get("task_type") or ""),"question":str(q or ""),"gold":str(row.get("answer") or row.get("gold") or row.get("solution") or row.get("ground_truth") or ""),"prediction":str(row.get("prediction") or row.get("pred") or row.get("response") or row.get("model_output") or ""),"images":list(row.get("images") or row.get("media") or []),"metadata":row.get("metadata") or {}}

class Runner:
    def __init__(self,a):
        self.backend=a.backend; self.model=str(a.model)
        if a.backend=="openai":
            from openai import OpenAI; self.client=OpenAI(api_key=a.api_key,base_url=a.base_url)
        else:
            from transformers import AutoProcessor
            from vllm import LLM,SamplingParams
            self.processor=AutoProcessor.from_pretrained(self.model,trust_remote_code=True); self.SamplingParams=SamplingParams
            self.llm=LLM(model=self.model,tensor_parallel_size=a.tensor_parallel_size,gpu_memory_utilization=a.gpu_memory_utilization,trust_remote_code=True,limit_mm_per_prompt={"image":8})
    @staticmethod
    def parse(text):
        text=re.sub(r"^```(?:json)?\s*|\s*```$","",text.strip()); s,e=text.find("{"),text.rfind("}")
        if s<0 or e<s: raise ValueError("no JSON object")
        return json.loads(text[s:e+1])
    def json(self,system,user,images=None,temperature=.2,max_tokens=2048):
        images=images or []
        if self.backend=="openai":
            from PIL import Image
            content=[{"type":"text","text":user}]
            for image_path in images:
                path=Path(image_path); path=path if path.is_absolute() else PROJECT_ROOT/path
                image=Image.open(path).convert("RGB"); buf=io.BytesIO(); image.save(buf,format="JPEG",quality=90)
                content.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()}})
            out=self.client.chat.completions.create(model=self.model,messages=[{"role":"system","content":system},{"role":"user","content":content}],temperature=temperature,max_tokens=max_tokens)
            return self.parse(out.choices[0].message.content or "")
        from qwen_vl_utils import process_vision_info
        content=[{"type":"text","text":user}]
        for image_path in images:
            path=Path(image_path); path=path if path.is_absolute() else PROJECT_ROOT/path; content.append({"type":"image","image":str(path.resolve())})
        messages=[{"role":"system","content":system},{"role":"user","content":content}]
        prompt=self.processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True); image_inputs,video_inputs=process_vision_info(messages); mm={}
        if image_inputs: mm["image"]=image_inputs
        if video_inputs: mm["video"]=video_inputs
        out=self.llm.generate([{"prompt":prompt,"multi_modal_data":mm}],self.SamplingParams(temperature=temperature,max_tokens=max_tokens),use_tqdm=False)
        return self.parse(out[0].outputs[0].text)

def classify(runner,bad):
    payload={"task_types":TASK_TYPES,"error_types":ERROR_TYPES,"scenario_tags":SCENARIO_TAGS,"bad_case":{"input_task":bad["task"],"question":bad["question"],"gold":bad["gold"],"prediction":bad["prediction"],"metadata":bad["metadata"]}}
    out=runner.json(CLASSIFY_SYSTEM,json.dumps(payload,ensure_ascii=False,separators=(",",":")),bad["images"],.1,1536)
    if out.get("task_type") not in TASK_TYPES: out["task_type"]=bad["task"] if bad["task"] in TASK_TYPES else "multimodal_financial_knowledge"
    if out.get("error_type") not in ERROR_TYPES: out["error_type"]="other_error"
    out["scenario_tags"]=[x for x in out.get("scenario_tags") or [] if x in SCENARIO_TAGS]
    return out

def fact_image(f):
    if f.get("source_mode")!="image": return ""
    images=list(f.get("images") or []); idx=f.get("image_index")
    if isinstance(idx,int) and 0<=idx<len(images): return images[idx]
    return images[0] if len(images)==1 else ""
def family(f):
    v=str(f.get("visual_type") or "").lower()
    if v in {"line_chart","bar_chart","pie_chart","area_chart","scatter_chart","chart"}: return "chart"
    if v in {"candlestick","kline","k_line","ohlc"}: return "candlestick"
    if v in {"relationship_diagram","ownership_diagram","relationship","equity_structure"}: return "relationship"
    if v in {"table","financial_table"}: return "table"
    return v or "other"
def allow_peer(cls): return cls["task_type"] in CROSS_COMPANY_TASKS or cls["error_type"] in CROSS_COMPANY_ERRORS or bool(set(cls.get("scenario_tags") or [])&CROSS_COMPANY_SCENARIOS)
def first(*xs): return next((str(x).strip() for x in xs if x not in (None,"","unknown")),"")
def doc_key(f): return first(f.get("document_entity_id"),f.get("document_id"),f.get("doc_id"),f.get("report_id"),str(f.get("source_ref") or "").split("#",1)[0]).lower()
def entity_key(f): return first(f.get("company_entity_id"),f.get("company_id"),f.get("company_name"),f.get("entity")).lower()
def industry_key(f):
    m=f.get("metadata") if isinstance(f.get("metadata"),dict) else {}; return first(f.get("industry_group"),f.get("industry_l2"),f.get("industry"),m.get("industry_group"),m.get("industry_l2"),m.get("industry")).lower()
def year(x):
    m=re.search(r"(?:19|20)\d{2}",str(x or "")); return int(m.group()) if m else None
def tier(anchors,candidate,cls):
    cd,ce,cp,ci,cy=doc_key(candidate),entity_key(candidate),str(candidate.get("period") or "").lower(),industry_key(candidate),year(candidate.get("period"))
    if cd and any(cd==doc_key(a) for a in anchors): return 0
    same=[a for a in anchors if ce and ce==entity_key(a)]
    if same:
        if cp and any(cp==str(a.get("period") or "").lower() for a in same): return 1
        if cy is not None and any(year(a.get("period")) is not None and abs(cy-year(a.get("period")))==1 for a in same): return 2
        return 3
    if allow_peer(cls) and ci and any(ci==industry_key(a) and ce and entity_key(a) and ce!=entity_key(a) for a in anchors): return 4
    return 99

def merge(policy,req):
    policy["min_images"]=max(policy["min_images"],int(req.get("min_images",0))); policy["min_text"]=max(policy["min_text"],int(req.get("min_text",0))); policy["min_pages"]=max(policy["min_pages"],int(req.get("min_pages",0))); policy["visual_numeric"]|=bool(req.get("visual_numeric"))
    for g in req.get("families") or []:
        g=sorted(set(g))
        if g not in policy["families"]: policy["families"].append(g)
def visual_policy(cls,prefer):
    p={"required":False,"preferred":bool(prefer),"preference_only":False,"text_only":False,"min_images":0,"min_text":0,"min_pages":0,"families":[],"visual_numeric":False,"allow_cross_company":allow_peer(cls)}
    if cls["task_type"] in TASK_VISUAL: merge(p,TASK_VISUAL[cls["task_type"]]); p["required"]=True
    if cls["error_type"] in VISUAL_ERRORS: merge(p,{"min_images":1}); p["required"]=True
    for s in cls.get("scenario_tags") or []:
        if s in SCENARIO_VISUAL:
            req=SCENARIO_VISUAL[s]; merge(p,req)
            if req.get("min_images") or req.get("families"): p["required"]=True
    if prefer and not p["required"]:
        p["required"]=True; p["preference_only"]=True; p["min_images"]=1; p["visual_numeric"]=cls["task_type"] in NUMERIC_TASKS
    elif not p["required"]: p["text_only"]=True
    return p

def score(f,cls,policy):
    s=float(f.get("confidence") or 0); e=cls["error_type"]
    if e in {"formula_selection_error","arithmetic_error","ratio_percentage_error","aggregation_error","reconciliation_error","multi_step_reasoning_error","comparison_error","ranking_error","temporal_reasoning_error","unit_scale_error","currency_error"} and f.get("numeric_value"): s+=2
    if policy["required"] and f.get("source_mode")=="image" and fact_image(f): s+=2
    for g in policy["families"]:
        if f.get("source_mode")=="image" and family(f) in g: s+=2
    if e=="period_confusion_error" and f.get("period"): s+=2
    if e=="scope_confusion_error" and (f.get("scope") or f.get("consolidation_scope")): s+=2
    if e in {"metric_confusion_error","statement_line_item_error"} and f.get("metric"): s+=2
    return s

def adjacency(edges):
    a=defaultdict(list)
    for e in edges:
        x,y=str(e.get("a") or e.get("source") or ""),str(e.get("b") or e.get("target") or ""); r=str(e.get("type") or e.get("relation") or "")
        if x and y: a[x].append((y,r)); a[y].append((x,r))
    return a
def policy_ok(facts,p):
    imgs={fact_image(f) for f in facts if fact_image(f)}
    if len(imgs)<p["min_images"] or sum(f.get("source_mode")=="text" for f in facts)<p["min_text"]: return False
    pages={f["page"] for f in facts if isinstance(f.get("page"),int)}
    if len(pages)<p["min_pages"]: return False
    fam={family(f) for f in facts if fact_image(f)}
    return all(bool(fam&set(g)) for g in p["families"])
def retrieve(rng,facts,fmap,adj,cls,max_facts,p):
    candidates=[f for f in facts if not (p["text_only"] and f.get("source_mode")=="image")]
    if not candidates: return None
    ranked=sorted(candidates,key=lambda f:(-score(f,cls,p),f["fact_id"])); seed=rng.choice(ranked[:min(30,len(ranked))]); selected=[seed]; ids={seed["fact_id"]}; edge_rows=[]; target=min(max_facts,8 if cls["task_type"] in NUMERIC_TASKS else 6)
    while len(selected)<target:
        front=[]
        for cur in selected:
            for other,rel in adj.get(cur["fact_id"],[]):
                if other in ids or other not in fmap: continue
                f=fmap[other]; t=tier(selected,f,cls)
                if t<99: front.append((t,-score(f,cls,p),cur["fact_id"],f,rel))
        if front:
            front.sort(key=lambda x:(x[0],x[1])); t,_,cur,f,rel=rng.choice(front[:min(20,len(front))]); selected.append(f); ids.add(f["fact_id"]); edge_rows.append({"a":cur,"b":f["fact_id"],"type":rel}); continue
        fallback=[f for f in ranked if f["fact_id"] not in ids and tier(selected,f,cls)<99]
        if not fallback: break
        f=rng.choice(fallback[:min(20,len(fallback))]); selected.append(f); ids.add(f["fact_id"])
    related=sorted((f for f in facts if f["fact_id"] not in ids and tier(selected,f,cls)<99 and not (p["text_only"] and f.get("source_mode")=="image")),key=lambda f:(tier(selected,f,cls),-score(f,cls,p),f["fact_id"]))
    def add(pred):
        nonlocal related
        for f in related:
            if pred(f): selected.append(f); ids.add(f["fact_id"]); related=[x for x in related if x["fact_id"]!=f["fact_id"]]; return True
        return False
    for g in p["families"]:
        if not any(fact_image(f) and family(f) in g for f in selected): add(lambda f,g=set(g): fact_image(f) and family(f) in g)
    while len({fact_image(f) for f in selected if fact_image(f)})<p["min_images"] and len(selected)<max_facts:
        existing={fact_image(f) for f in selected if fact_image(f)}
        if not add(lambda f,existing=existing: fact_image(f) and fact_image(f) not in existing): break
    while sum(f.get("source_mode")=="text" for f in selected)<p["min_text"] and len(selected)<max_facts:
        if not add(lambda f:f.get("source_mode")=="text"): break
    while len({f["page"] for f in selected if isinstance(f.get("page"),int)})<p["min_pages"] and len(selected)<max_facts:
        pages={f["page"] for f in selected if isinstance(f.get("page"),int)}
        if not add(lambda f,pages=pages:isinstance(f.get("page"),int) and f["page"] not in pages): break
    return (selected[:max_facts],edge_rows) if policy_ok(selected[:max_facts],p) else None

def collect_images(facts):
    out=[]
    for f in facts:
        im=fact_image(f)
        if im and im not in out: out.append(im)
        if len(out)>=8: break
    return out
def gen_rule(e):
    if e in CONFUSION_ERRORS: return "加入与正确证据高度相似的真实干扰项，训练排除错误实体/期间/口径/指标/单位。"
    if e in VISUAL_ERRORS: return "必须直接使用新的金融原图构题，视觉证据不可被题面文本替代。"
    if e in {"formula_selection_error","arithmetic_error","ratio_percentage_error","aggregation_error","reconciliation_error","multi_step_reasoning_error"}: return "构造可程序验证的金融数值/推理题。"
    if e in {"unsupported_inference_error","insufficient_evidence_handling_error","over_refusal_error"}: return "构造证据边界数据，覆盖可回答与材料不足。"
    return "使用新的真实金融证据构造同一错误能力的新样本，禁止只改写原bad case。"
def payload(bad,cls,facts,edges,p,mode):
    rows=[]; n=0
    for f in facts:
        x={k:v for k,v in f.items() if k!="images"}
        if f.get("numeric_value"): x["variable"]=f"v{n}"; n+=1
        rows.append(x)
    return json.dumps({"source_badcase":{"question":bad["question"],"gold":bad["gold"],"prediction":bad["prediction"]},"classification":cls,"generation_rule":gen_rule(cls["error_type"]),"scenario_mode":mode,"visual_policy":p,"facts":rows,"edges":edges},ensure_ascii=False,separators=(",",":"))

ALLOWED={Decimal(x) for x in ("0","1","2","4","12","100","360","365","10000","100000000")}; NUM_RE=re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
def decimal_text(x):
    try:return format(Decimal(str(x or "").replace(",","")),"f")
    except InvalidOperation:return ""
def eval_expr(expr,vals):
    tree=ast.parse(expr,mode="eval")
    def visit(n):
        if isinstance(n,ast.Expression): return visit(n.body)
        if isinstance(n,ast.Name) and n.id in vals:return vals[n.id]
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):
            v=Decimal(str(n.value))
            if v not in ALLOWED: raise ValueError("constant")
            return v
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,(ast.UAdd,ast.USub)):
            v=visit(n.operand); return v if isinstance(n.op,ast.UAdd) else -v
        if isinstance(n,ast.BinOp) and isinstance(n.op,(ast.Add,ast.Sub,ast.Mult,ast.Div)):
            a,b=visit(n.left),visit(n.right); return a+b if isinstance(n.op,ast.Add) else a-b if isinstance(n.op,ast.Sub) else a*b if isinstance(n.op,ast.Mult) else a/b
        raise ValueError("expr")
    return visit(tree)
def verify(candidate,facts,cls,p):
    if candidate.get("status")!="accepted": return False,"generator_rejected"
    fmap={f["fact_id"]:f for f in facts}; evidence=list(dict.fromkeys(candidate.get("evidence_ids") or [])); negatives=list(dict.fromkeys(candidate.get("hard_negative_ids") or []))
    if not evidence or any(x not in fmap for x in evidence): return False,"invalid_evidence"
    if any(x not in fmap for x in negatives): return False,"invalid_negative"
    if cls["error_type"] in CONFUSION_ERRORS and not negatives:return False,"negative_required"
    used=[fmap[x] for x in evidence]
    if p["required"]:
        visual=set(candidate.get("visual_evidence_ids") or [])
        if not visual or not visual.issubset(set(evidence)) or not policy_ok(used,p): return False,"visual_policy"
    program=candidate.get("program") or []
    if cls["task_type"] in NUMERIC_TASKS:
        if not program:return False,"numeric_program_missing"
        alias={}; i=0
        for f in facts:
            if f.get("numeric_value"): alias[f"v{i}"]=f; i+=1
        vals={a:Decimal(str(f["numeric_value"])) for a,f in alias.items() if f["fact_id"] in evidence}; last=None; visual_program=set()
        for j,step in enumerate(program,1):
            names={n.id for n in ast.walk(ast.parse(str(step.get("expression") or ""),mode="eval")) if isinstance(n,ast.Name)}
            if any(n not in vals for n in names):return False,"unknown_variable"
            for n in names:
                if n in alias and alias[n].get("source_mode")=="image": visual_program.add(fact_image(alias[n]))
            try:r=eval_expr(str(step["expression"]),vals); c=Decimal(decimal_text(step.get("claimed_result")))
            except Exception:return False,"invalid_program"
            if abs(r-c)>max(Decimal(".000001"),abs(r)*Decimal(".000001")):return False,"program_mismatch"
            vals[f"s{j}"]=r; last=r
        nums=[Decimal(x.replace(",","")) for x in NUM_RE.findall(str(candidate.get("answer") or ""))]
        if last is None or len(nums)!=1 or abs(nums[0]-last)>max(Decimal(".000001"),abs(last)*Decimal(".000001")):return False,"answer_mismatch"
        if p["visual_numeric"] and len({x for x in visual_program if x})<p["min_images"]:return False,"visual_numeric_not_grounded"
    return (True,"accepted") if str(candidate.get("question") or "").strip() and str(candidate.get("answer") or "").strip() else (False,"empty")
def sim(a,b):
    A=set(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+",a.lower()));B=set(re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+",b.lower()));return len(A&B)/len(A|B) if A and B else 0

def render(candidate,facts):
    fmap={f["fact_id"]:f for f in facts}; ids=list(dict.fromkeys((candidate.get("evidence_ids") or [])+(candidate.get("hard_negative_ids") or []))); ctx=[fmap[x] for x in ids if x in fmap]; images=collect_images(ctx); pos={x:i+1 for i,x in enumerate(images)}; lines=[]
    for i,f in enumerate(ctx,1):
        page=f"第{f['page']}页" if isinstance(f.get("page"),int) else str(f.get("source_ref") or "")
        if f.get("source_mode")=="image" and fact_image(f) in pos: lines.append(f"[E{i}] {page}，对应图片{pos[fact_image(f)]}，请直接查看图片。")
        else: lines.append(f"[E{i}] {page}：{f.get('evidence_quote') or f.get('value_text') or ''}")
    return "<image>"*len(images)+"参考材料：\n"+"\n".join(lines)+"\n\n问题："+candidate["question"],images
def rows_for(bad,cls,candidate,facts,judge,p,mode):
    prompt,images=render(candidate,facts); reasoning="\n".join(map(str,candidate.get("reasoning_steps") or [])); answer=str(candidate["answer"]); response=f"{reasoning}\n\n答案：{answer}" if reasoning else answer; sample=sid("flywheel",bad["badcase_id"],cls["error_type"],candidate["question"])
    meta={"synthetic_method":"badcase_taxonomy_flywheel_v4","source_badcase_id":bad["badcase_id"],"source_error_file":bad["source_file"],"classification":cls,"scenario_mode":mode,"visual_policy":p,"evidence_ids":candidate.get("evidence_ids") or [],"hard_negative_ids":candidate.get("hard_negative_ids") or [],"judge":judge}
    sft={"sample_id":sample,"messages":[{"role":"user","content":prompt},{"role":"assistant","content":response}],"source":"badcase_flywheel","split":"train","images":images,"task":candidate["task_type"],"metadata":meta}; rl=None
    if cls["task_type"] in NUMERIC_TASKS:
        rl={"sample_id":sample,"messages":[{"role":"user","content":prompt}],"source":"badcase_flywheel","split":"train","images":images,"task":candidate["task_type"],"output_format":"number_or_free_text","solution":answer,"metadata":meta,"reward_type":"rule","reward_subtype":"numeric","verifier_type":"numeric","_reward_routing":{"version":"badcase_taxonomy_flywheel_v4","reason":"badcase_targeted_program_verified"}}
    return sft,rl

def main():
    a=parse_args(); rng=random.Random(a.seed); a.output_root.mkdir(parents=True,exist_ok=True); raw=list(iter_errors(a.error_root)); raw=raw[:a.max_cases] if a.max_cases else raw; bads=[normalize_bad(*x) for x in raw]; facts=read_jsonl(a.facts); edges=read_jsonl(a.edges); fmap={f["fact_id"]:f for f in facts}; adj=adjacency(edges); runner=Runner(a)
    classes=[]; variants=[]; sfts=[]; rls=[]; rejected=[]; counts=Counter(); seen=[]
    for bad in bads:
        try: cls=classify(runner,bad)
        except Exception as e: rejected.append({"badcase_id":bad["badcase_id"],"stage":"classify","error":str(e)}); counts["classify_error"]+=1; continue
        classes.append({"badcase_id":bad["badcase_id"],"source_file":bad["source_file"],"classification":cls}); counts[f"error:{cls['error_type']}"]+=1; accepted=0
        for _ in range(a.variants_per_case*a.attempt_multiplier):
            if accepted>=a.variants_per_case: break
            mode="cross_scenario_transfer" if rng.random()<a.cross_scenario_ratio else "same_or_similar_scenario"; p=visual_policy(cls,rng.random()<a.prefer_visual_ratio); sampled=retrieve(rng,facts,fmap,adj,cls,a.max_facts,p)
            if sampled is None and p.get("preference_only"):
                p=visual_policy(cls,False); sampled=retrieve(rng,facts,fmap,adj,cls,a.max_facts,p); counts["visual_fallback_to_text"]+=int(sampled is not None)
            if sampled is None: counts["no_neighborhood"]+=1; continue
            picked,picked_edges=sampled; images=collect_images(picked)
            try:c=runner.json(SYNTH_SYSTEM,payload(bad,cls,picked,picked_edges,p,mode),images,.55,4096)
            except Exception as e: rejected.append({"badcase_id":bad["badcase_id"],"stage":"synthesize","error":str(e)}); counts["synthesis_error"]+=1; continue
            ok,reason=verify(c,picked,cls,p)
            if not ok: counts[reason]+=1; continue
            if sim(c["question"],bad["question"])>.72 or any(sim(c["question"],q)>.86 for q in seen[-2000:]): counts["duplicate_or_too_similar"]+=1; continue
            jp=json.dumps({"classification":cls,"visual_policy":p,"source_badcase_question":bad["question"],"candidate":c,"facts":[{k:v for k,v in f.items() if k!="images"} for f in picked]},ensure_ascii=False,separators=(",",":"))
            try:j=runner.json(VERIFY_SYSTEM,jp,images,.1,1536)
            except Exception as e: rejected.append({"badcase_id":bad["badcase_id"],"stage":"judge","error":str(e)}); counts["judge_error"]+=1; continue
            if j.get("supported") is not True or j.get("targets_failure") is not True or j.get("answerable") is not True or j.get("novel") is not True or int(j.get("score") or 0)<a.min_judge_score or (p["required"] and j.get("visual_required") is not True): counts["judge_rejected"]+=1; continue
            sft,rl=rows_for(bad,cls,c,picked,j,p,mode); sfts.append(sft); rls.extend([rl] if rl else []); variants.append({"sample_id":sft["sample_id"],"source_badcase_id":bad["badcase_id"],"classification":cls,"scenario_mode":mode,"candidate":c,"judge":j}); seen.append(c["question"]); accepted+=1; counts["accepted"]+=1; counts["accepted_visual" if sft["images"] else "accepted_text_only"]+=1
    write_jsonl(a.output_root/"badcase_classification.jsonl",classes); write_jsonl(a.output_root/"variants.jsonl",variants); write_jsonl(a.output_root/"train_sft_badcase.jsonl",sfts); write_jsonl(a.output_root/"train_sft_badcase_visual.jsonl",[x for x in sfts if x["images"]]); write_jsonl(a.output_root/"train_sft_badcase_text.jsonl",[x for x in sfts if not x["images"]]); write_jsonl(a.output_root/"train_rl_badcase.jsonl",rls); write_jsonl(a.output_root/"rejected.jsonl",rejected)
    audit={"method":"badcase_taxonomy_flywheel_v4","bad_cases":len(bads),"accepted_sft":len(sfts),"accepted_rl":len(rls),"prefer_visual_ratio":a.prefer_visual_ratio,"evidence_retrieval_hierarchy":["same_document","same_entity_same_period","same_entity_adjacent_period","same_entity_other_period","same_industry_peer_if_explicitly_allowed"],"counts":dict(counts)}; (a.output_root/"audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
