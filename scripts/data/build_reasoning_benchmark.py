#!/usr/bin/env python3
"""Build the 24-task reasoning benchmark from the current 240-row benchmark.

Three open-ended / format-sensitive benchmark tasks are converted into
deterministic reasoning targets while preserving the original 24 x 10 shape:

- financial_visual_description -> financial_visual_data_reasoning
- financial_summarization -> financial_reason_explanation
- financial_entity_relation_extraction -> financial_entity_relation_recognition

The original training tasks are not deleted; this script only changes the
derived evaluation benchmark.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


VISUAL_SOURCE_TASK = "financial_visual_description"
VISUAL_TARGET_TASK = "financial_visual_data_reasoning"
SUMMARY_SOURCE_TASK = "financial_summarization"
SUMMARY_TARGET_TASK = "financial_reason_explanation"
ENTITY_SOURCE_TASK = "financial_entity_relation_extraction"
ENTITY_TARGET_TASK = "financial_entity_relation_recognition"


_VISUAL_REPLACEMENTS: dict[str, tuple[str, str]] = {
    "MME-Finance/Image Caption/763": (
        "根据图中列出的四只超跌绩优股及其年内跌幅，计算四者年内跌幅的简单平均值。仅输出百分比，保留两位小数。",
        "38.44%",
    ),
    "MME-Finance/Image Caption/319": (
        "根据图中数据，计算田中精机与创新新材涨幅的差值。仅输出数值，单位为个百分点，保留两位小数。",
        "9.91",
    ),
    "MME-Finance/Image Caption/0": (
        "根据图中2024年3月13日苹果公司的最高价和最低价，计算当日日内价差。仅输出数值，保留三位小数。",
        "2.425",
    ),
    "MME-Finance/Image Caption/565": (
        "根据图中的上涨股票数和下跌股票数，计算净上涨家数（上涨数减下跌数）。仅输出整数。",
        "1962",
    ),
    "MME-Finance/Image Caption/140": (
        "根据图中的BOLL上轨和下轨最新值，计算BOLL带宽（上轨减下轨）。仅输出数值，保留三位小数。",
        "15.886",
    ),
    "MME-Finance/Image Caption/1013": (
        "根据图中深圳成指的开盘价和当前价，计算当前价较开盘价低多少点。仅输出数值，保留两位小数。",
        "9.41",
    ),
    "MME-Finance/Image Caption/775": (
        "根据图中文字，统计被明确点名为“大涨”或“跟涨”的一体成型电感概念股数量。仅输出整数。",
        "5",
    ),
    "MME-Finance/Image Caption/333": (
        "根据图中股票数据表的表头，统计明确列出的字段数量。仅输出整数。",
        "5",
    ),
    "MME-Finance/Image Caption/1": (
        "根据图中2024年6月25日苹果公司的最高价和最低价，计算当日日内价差。仅输出数值，保留两位小数。",
        "2.77",
    ),
    "MME-Finance/Image Caption/579": (
        "根据图中四个中国股指的当日涨跌幅，计算最大涨幅与最小涨幅之间的差值。仅输出数值，单位为个百分点，保留两位小数。",
        "0.96",
    ),
}


_SUMMARY_REPLACEMENTS: dict[str, tuple[str, str]] = {
    "generated_hard_v3/financial_summarization/001": (
        "某零部件制造商2025年收入同比增长12%，其中销量+9%、价格/组合+3%；毛利率由31.2%降至28.6%，主要因新工厂爬坡和铜价上涨。净利润同比+18%，但包含出售闲置土地税后收益1.4亿元；剔除后调整后净利润下降4%。经营现金流由9.1亿元降至5.8亿元，应收账款天数从47天升至63天。公司维持收入指引但下调毛利率指引。以下哪项最准确解释当前盈利质量？\nA. 核心盈利弱于报表净利，利润受一次性处置收益抬高，且现金质量恶化\nB. 核心盈利改善主要来自土地处置，经营现金流同步增强\nC. 毛利率下降主要由销量下滑造成，但现金回款明显改善\nD. 收入和利润均由可持续提价驱动，后续风险较低\n仅输出选项字母。",
        "A",
    ),
    "generated_hard_v3/financial_summarization/002": (
        "某SaaS公司季度收入同比+24%、ARR同比+29%，但新签ACV仅+8%，净留存率从118%降至111%。剔除一笔提前确认的实施收入后，收入增速约19%。自由现金流由-0.4亿元转正至0.6亿元，其中约0.5亿元来自数据中心设备款延期支付。管理层维持ARR目标，但下调新签订单指引。以下哪项最准确描述增长和现金流质量？\nA. 新签和净留存同步加速，FCF转正主要来自经营性改善\nB. ARR增长较快，但领先指标走弱，FCF改善又高度依赖付款时点，增长兑现风险上升\nC. ARR和新签订单均显著下滑，因此公司已经进入收入负增长\nD. 新签订单指引上调，说明客户审批周期缩短\n仅输出选项字母。",
        "B",
    ),
    "generated_hard_v3/financial_summarization/003": (
        "某银行净利润同比+6%，净利息收入-4%，净息差由2.08%降至1.84%；手续费收入+15%，主要来自一次性大型债券承销。信用减值同比+38%，商业地产贡献超过一半新增拨备，关注类贷款率由1.7%升至2.4%。CET1由11.9%降至11.3%，仍高于内部目标。以下哪项是最重要的盈利质量判断？\nA. 净利润增长完全由可持续净息差扩张驱动\nB. 手续费增长足以证明信用风险已经下降\nC. 一次性手续费支撑利润，同时NIM和资产质量恶化，资本缓冲也有所收窄\nD. CET1高于内部目标意味着商业地产风险可以忽略\n仅输出选项字母。",
        "C",
    ),
    "generated_hard_v3/financial_summarization/004": (
        "某零售商收入同比+7%，其中同店销售+2%、新店贡献+5%；客单价+4%但客流-2%。毛利率由36.5%升至37.3%，改善来自汇率和折扣率下降。期末库存同比+18%，经营现金流同比下降22%。若秋季客流不恢复，公司可能在四季度提高促销力度。以下哪项最准确描述当前经营风险？\nA. 收入增长主要来自客流恢复，库存增速低于销售\nB. 毛利率改善完全来自销量提升，因此可以直接外推\nC. CFO下降主要因为供应商延长付款期限，对库存没有影响\nD. 增长更多依赖新店，客流仍弱且库存偏高，后续促销可能侵蚀当前毛利率\n仅输出选项字母。",
        "D",
    ),
    "generated_hard_v3/financial_summarization/005": (
        "某工业公司收入+5%，其中价格+6%、销量-1%；调整后EBIT率由14.2%降至12.9%。订单收入比由1.18降至0.91，在手订单同比+10%，但约四成为两年前签订的低毛利固定价合同。经营现金流同比+30%，主要因客户预付款增加；报表净利润还包含出售非核心子公司收益。以下哪项最准确解释当前周期位置？\nA. 收入仍由价格支撑，但订单动能和利润率走弱，现金改善与报表利润均含较强时点/一次性因素\nB. 订单收入比上升说明需求正在加速，低毛利旧合同已基本消化\nC. CFO改善主要来自库存和应收的结构性优化\nD. 销量增长是收入增长的主要来源，利润率同步扩张\n仅输出选项字母。",
        "A",
    ),
    "generated_hard_v3/financial_summarization/006": (
        "根据图1的利润表与调整项目、图2的经营现金流和全年指引，以下哪项最准确描述公司的核心盈利与现金质量？\nA. 报表净利和核心净利均明显改善，CFO同步增强\nB. 剔除处置收益后核心净利下降，CFO和应收表现也弱，指引修复依赖良率和原料价格\nC. 核心净利下降主要因为所得税上升，与毛利率无关\nD. 毛利率指引上调且原料风险已经完全套保\n仅输出选项字母。",
        "B",
    ),
    "generated_hard_v3/financial_summarization/007": (
        "根据图1的分部收入/利润率与订单、图2的自由现金流桥接和下半年指引，以下哪项最准确描述业务组合与现金流质量？\nA. 高毛利软件增速显著快于硬件，因此集团利润率受到结构性提升\nB. 硬件增长较慢但利润率更高，FCF改善来自应收下降\nC. 收入结构向低毛利硬件倾斜，利润率承压；FCF改善又较多来自资本开支延期\nD. 软件续约和硬件成本均已锁定，因此下半年没有明显兑现风险\n仅输出选项字母。",
        "C",
    ),
    "generated_hard_v3/financial_summarization/008": (
        "根据图1的银行净息差、手续费和信用成本，以及图2的资产质量、CET1和管理层展望，以下哪项最准确描述盈利质量和主要风险？\nA. 一次性承销费支撑手续费增长，但NIM收窄、信用成本和关注类贷款上升，资产质量仍是主要风险\nB. NIM扩张与信用成本下降共同推动可持续盈利改善\nC. CET1下降至内部目标以下，银行已经不满足资本要求\nD. 商业地产风险下降，因此管理层下调信用成本指引\n仅输出选项字母。",
        "A",
    ),
    "generated_hard_v3/financial_summarization/009": (
        "根据图1的保险公司保费、综合成本率和投资收益，以及图2的巨灾损失、准备金释放和全年指引，以下哪项最准确描述基础承保表现？\nA. 基础综合成本率改善，报表利润未受准备金释放影响\nB. 巨灾损失下降且费率提升已经完全覆盖赔付通胀\nC. 投资收益下降是唯一拖累，承保业务本身明显改善\nD. 基础承保表现恶化，准备金释放对报表利润形成支撑，全年结果仍高度依赖巨灾频率与费率充分性\n仅输出选项字母。",
        "D",
    ),
    "generated_hard_v3/financial_summarization/010": (
        "根据图1的ARR、净留存率和新签订单，以及图2的自由现金流构成和管理层指引，以下哪项最准确描述下一阶段增长风险？\nA. 净留存率和新签订单同步改善，说明增长前置指标增强\nB. ARR仍高增，但净留存和新签放缓；FCF转正又主要来自付款延期，后续增长面临审批周期风险\nC. FCF转正完全来自毛利率改善，与付款时点无关\nD. 管理层上调新签订单指引，因此未来增长确定性提高\n仅输出选项字母。",
        "B",
    ),
}


_ENTITY_REPLACEMENTS: dict[str, tuple[str, str]] = {
    "generated_hard_v3/financial_entity_extraction/001": (
        "以下实体中，哪一家是直接参与本次收购并承担专项审阅工作的审计机构？\nA. 北河银行\nB. 华陆证券\nC. 云数智能有限公司\nD. 中衡会计师事务所\n仅输出选项字母。",
        "D",
    ),
    "generated_hard_v3/financial_entity_extraction/005": (
        "以下哪一家机构在债务重组完成后实施了主体评级上调？\nA. 海东银行\nB. 辰海纾困基金\nC. 华南评级有限公司\nD. 远洋装备有限公司\n仅输出选项字母。",
        "C",
    ),
    "generated_hard_v3/financial_entity_extraction/006": (
        "根据两张图，直接参与本次资产出售的实体中，哪一个属于FUND？\nA. 东澜科技股份有限公司\nB. 北辰产业基金\nC. 东澜数据有限公司\nD. 海岳证券\n仅输出选项字母。",
        "B",
    ),
    "generated_hard_v3/financial_entity_extraction/008": (
        "根据并购交割公告和服务机构清单，哪一家是本次交易的专项审计机构？\nA. 华中银行\nB. 国衡证券\nC. 青禾自动化有限公司\nD. 德正会计师事务所\n仅输出选项字母。",
        "D",
    ),
    "generated_hard_v3/financial_entity_extraction/010": (
        "根据基金投资公告和交割资金安排，哪一家银行直接参与了本轮资金交割？\nA. 远见资本管理有限公司\nB. 远见成长三期基金\nC. 南海银行\nD. 博澜机器人有限公司\n仅输出选项字母。",
        "C",
    ),
    "generated_hard_v3/financial_relation_extraction/001": (
        "根据材料，截至报告日以下哪项关系仍然有效且被明确支持？\nA. 曜石控股 PLEDGES_TO 东城银行\nB. 甲证券 UNDERWRITES 青岚科技\nC. 新港银行 LENDS_TO 青岚科技\nD. 国新基金 OWNS 青岚科技\n仅输出选项字母。",
        "C",
    ),
    "generated_hard_v3/financial_relation_extraction/005": (
        "根据材料，截至报告日以下哪项关系应被保留？\nA. 国新基金 OWNS 北辰科技\nB. 林峰 PLEDGES_TO 海城银行\nC. 北辰科技 OWNS 北辰云\nD. 南方银行 PLEDGES_TO 北辰云\n仅输出选项字母。",
        "B",
    ),
    "generated_hard_v3/financial_relation_extraction/006": (
        "根据两张图，新港银行与青岚科技之间被明确支持的有效关系类型是什么？\nA. OWNS\nB. CONTROLS\nC. LENDS_TO\nD. PLEDGES_TO\n仅输出选项字母。",
        "C",
    ),
    "generated_hard_v3/financial_relation_extraction/008": (
        "根据担保与质押登记以及贷款合同状态，凌云控股与凌云物流之间的有效关系类型是什么？\nA. GUARANTEES_FOR\nB. LENDS_TO\nC. OWNS\nD. ACQUIRES\n仅输出选项字母。",
        "A",
    ),
    "generated_hard_v3/financial_relation_extraction/010": (
        "根据重组后的控制链，国盛集团与海川装备之间被明确支持的关系类型是什么？\nA. LENDS_TO\nB. CONTROLS\nC. PLEDGES_TO\nD. UNDERWRITES\n仅输出选项字母。",
        "B",
    ),
}


_TRANSFORMS: dict[str, tuple[str, dict[str, tuple[str, str]], str]] = {
    VISUAL_SOURCE_TASK: (VISUAL_TARGET_TASK, _VISUAL_REPLACEMENTS, "visual_data_reasoning"),
    SUMMARY_SOURCE_TASK: (SUMMARY_TARGET_TASK, _SUMMARY_REPLACEMENTS, "reason_explanation"),
    ENTITY_SOURCE_TASK: (ENTITY_TARGET_TASK, _ENTITY_REPLACEMENTS, "entity_relation_recognition"),
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise TypeError(f"{path}:{line_number}: row must be a JSON object")
            rows.append(row)
    return rows


def _validate_shape(rows: list[dict[str, Any]], *, stage: str) -> Counter[str]:
    if len(rows) != 240:
        raise ValueError(f"{stage}: expected 240 rows, got {len(rows)}")
    counts = Counter(str(row.get("task") or "") for row in rows)
    if len(counts) != 24 or set(counts.values()) != {10}:
        raise ValueError(f"{stage}: expected 24 tasks x 10 rows, got {dict(counts)}")
    for index, row in enumerate(rows, 1):
        messages = row.get("messages") or []
        if not messages or messages[0].get("role") != "user" or messages[-1].get("role") != "assistant":
            raise ValueError(f"{stage}: row {index} has invalid messages")
        prompt = str(messages[0].get("content") or "")
        images = list(row.get("images") or [])
        if prompt.count("<image>") != len(images):
            raise ValueError(
                f"{stage}: row {index} image marker mismatch: "
                f"{prompt.count('<image>')} markers vs {len(images)} images"
            )
    return counts


def _prompt_with_images(row: dict[str, Any], question: str) -> str:
    image_count = len(row.get("images") or [])
    if image_count == 0:
        return question
    return "".join("<image>\n" for _ in range(image_count)) + question


def transform(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    input_counts = _validate_shape(rows, stage="input")
    for source_task, (target_task, replacements, _) in _TRANSFORMS.items():
        if input_counts.get(source_task) != 10:
            raise ValueError(
                f"input: expected exactly 10 {source_task!r} rows, "
                f"got {input_counts.get(source_task, 0)}"
            )
        if input_counts.get(target_task, 0):
            raise ValueError(f"input already contains target task {target_task!r}; refusing to transform twice")
        if len(replacements) != 10:
            raise ValueError(f"internal: expected 10 replacements for {source_task!r}, got {len(replacements)}")

    seen: dict[str, set[str]] = {task: set() for task in _TRANSFORMS}
    output: list[dict[str, Any]] = []

    for row in rows:
        source_task = str(row.get("task") or "")
        spec = _TRANSFORMS.get(source_task)
        if spec is None:
            output.append(row)
            continue

        target_task, replacements, source_suffix = spec
        source = str(row.get("source") or "")
        replacement = replacements.get(source)
        if replacement is None:
            raise ValueError(f"unexpected {source_task} source: {source!r}")
        if source in seen[source_task]:
            raise ValueError(f"duplicate {source_task} source: {source!r}")
        seen[source_task].add(source)

        question, answer = replacement
        updated = copy.deepcopy(row)
        updated["messages"] = [
            {"role": "user", "content": _prompt_with_images(updated, question)},
            {"role": "assistant", "content": answer},
        ]
        updated["source"] = f"derived/{source}/{source_suffix}"
        updated["task"] = target_task
        output.append(updated)

    for source_task, (_, replacements, _) in _TRANSFORMS.items():
        missing = sorted(set(replacements) - seen[source_task])
        if missing:
            raise ValueError(f"missing expected {source_task} sources: {missing}")

    output_counts = _validate_shape(output, stage="output")
    for source_task, (target_task, _, _) in _TRANSFORMS.items():
        if source_task in output_counts:
            raise ValueError(f"output still contains {source_task}")
        if output_counts.get(target_task) != 10:
            raise ValueError(f"output: expected 10 {target_task} rows")
    return output


def _write_jsonl_atomic(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = transform(_load_jsonl(args.input))
    _write_jsonl_atomic(args.output, rows)
    counts = Counter(str(row["task"]) for row in rows)
    print(
        f"wrote {args.output}: rows={len(rows)} tasks={len(counts)} "
        f"{VISUAL_TARGET_TASK}={counts[VISUAL_TARGET_TASK]} "
        f"{SUMMARY_TARGET_TASK}={counts[SUMMARY_TARGET_TASK]} "
        f"{ENTITY_TARGET_TASK}={counts[ENTITY_TARGET_TASK]}"
    )


if __name__ == "__main__":
    main()
