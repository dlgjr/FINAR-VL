"""Deterministic task sampling plans for SFT."""

from __future__ import annotations

import argparse
import collections
import json
import multiprocessing
import os
import random
import time
from pathlib import Path
from typing import Any, Iterator


DEFAULT_MULTI_RATIO = 0.40
ALPHA_SCHEDULE = ((0, 800, 0.55), (800, 2000, 0.50), (2000, float("inf"), 0.45))
TOKEN_LENGTH_BETA = 0.5
MIN_ASSISTANT_TOKENS_FOR_WEIGHT = 8
MAX_MULTI_EFFECTIVE_TOKEN_RATIO = 0.60
MULTI_UPWEIGHT = {
    "cross_modal_multi_hop": 2.5,
    "multimodal_financial_knowledge": 2.5,
    "multi_step_numerical_reasoning": 2.4,
    "financial_scenario_sensitivity_analysis": 2.4,
    "valuation_reasoning": 2.4,
    "financial_consistency_error_detection": 2.3,
    "financial_evidence_reconciliation": 2.3,
    "financial_counterfactual_inference": 2.3,
    "financial_definition_scope_reasoning": 2.2,
    "temporal_financial_reasoning": 2.2,
    "relationship_equity_structure": 2.2,
    "evidence_retrieval": 2.2,
    "risk_sentiment_policy": 2.0,
    "compliance_safety_suitability": 1.5,
    "portfolio_allocation_risk_return": 1.5,
}
TEXT_UPWEIGHT = {
    "valuation_reasoning": 2.2,
    "financial_scenario_sensitivity_analysis": 2.2,
    "financial_evidence_reconciliation": 2.2,
    "financial_causal_event_reasoning": 2.1,
    "financial_counterfactual_inference": 2.1,
    "financial_definition_scope_reasoning": 2.1,
    "temporal_financial_reasoning": 2.1,
    "financial_consistency_error_detection": 2.1,
    "multi_step_numerical_reasoning": 2.0,
    "relationship_equity_structure": 2.0,
    "risk_sentiment_policy": 2.0,
    "single_table_qa": 2.0,
    "financial_relation_extraction": 1.6,
    "financial_entity_extraction": 1.5,
    "financial_audit_fundamentals": 1.5,
    "compliance_safety_suitability": 1.5,
    "portfolio_allocation_risk_return": 1.5,
    "evidence_retrieval": 1.2,
}
MULTI_DOWNWEIGHT = {
    "document_fact_extraction": 0.50,
    "statistics_comparison_ranking": 0.35,
    "chart_data_extraction": 0.40,
    "basic_arithmetic_metrics": 0.40,
    "entity_extraction_classification": 0.50,
    "table_counting": 0.50,
    "image_caption": 0.25,
    "chart_statement_verification": 0.65,
}
TEXT_DOWNWEIGHT = {
    "financial_event_extraction": 0.35,
    "financial_headline_classification": 0.20,
    "stock_movement_prediction": 0.15,
    "financial_sentiment_analysis": 0.45,
    "economic_law": 0.60,
    "general_dialogue": 0.50,
}
PRIORITY_SMALL_TASKS = frozenset({
    "cross_modal_multi_hop",
    "multimodal_financial_knowledge",
    "multi_step_numerical_reasoning",
    "financial_scenario_sensitivity_analysis",
    "valuation_reasoning",
    "financial_consistency_error_detection",
    "financial_evidence_reconciliation",
    "financial_counterfactual_inference",
    "financial_definition_scope_reasoning",
    "temporal_financial_reasoning",
    "relationship_equity_structure",
    "evidence_retrieval",
    "risk_sentiment_policy",
    "single_table_qa",
    "financial_causal_event_reasoning",
})
TASK_TO_FAMILY = {'accounting_cost_reasoning': 'accounting_valuation',
 'administrative_law_reasoning': 'risk_policy_advice',
 'anomaly_information_tracing': 'retrieval_grounding',
 'asset_pricing_model_calculation': 'accounting_valuation',
 'bank_customer_service_intent_classification': 'classification_sentiment',
 'bank_reserve_requirement_calculation': 'accounting_valuation',
 'basic_arithmetic_metrics': 'numerical_statistics',
 'business_strategy_analysis': 'generation_dialogue',
 'candlestick_time_series': 'chart_reasoning',
 'capital_budgeting_calculation': 'accounting_valuation',
 'cash_management_calculation': 'accounting_valuation',
 'chart_arithmetic_reasoning': 'chart_reasoning',
 'chart_counting': 'chart_reasoning',
 'chart_data_extraction': 'chart_reasoning',
 'chart_legend_identification': 'chart_reasoning',
 'chart_statement_verification': 'chart_reasoning',
 'chart_trend_inference': 'chart_reasoning',
 'chart_visual_property_reasoning': 'chart_reasoning',
 'climate_transition_inference': 'risk_policy_advice',
 'commercial_bank_finance': 'financial_knowledge',
 'compliance_safety_suitability': 'risk_policy_advice',
 'compositional_reasoning': 'numerical_statistics',
 'corporate_finance_and_deals': 'accounting_valuation',
 'corporate_strategy_inference': 'generation_dialogue',
 'cost_accounting_calculation': 'accounting_valuation',
 'cost_accounting_variance_reasoning': 'accounting_valuation',
 'cost_volume_profit_calculation': 'accounting_valuation',
 'counterfactual_reasoning': 'market_macro_reasoning',
 'criminal_law_reasoning': 'risk_policy_advice',
 'cross_modal_multi_hop': 'multipage_financial_reasoning',
 'derivatives_analysis': 'accounting_valuation',
 'descriptive_statistics_calculation': 'numerical_statistics',
 'digital_asset_analysis': 'financial_knowledge',
 'div_policies': 'financial_knowledge',
 'document_arithmetic_reasoning': 'numerical_statistics',
 'document_comparative_explanation': 'generation_dialogue',
 'document_comparison': 'generation_dialogue',
 'document_counting': 'document_perception',
 'document_explanation': 'generation_dialogue',
 'document_fact_extraction': 'information_extraction',
 'document_function_extraction': 'information_extraction',
 'document_inference': 'generation_dialogue',
 'document_multi_span_extraction': 'information_extraction',
 'document_numeric_extraction': 'information_extraction',
 'document_opinion_interpretation': 'generation_dialogue',
 'document_policy_explanation': 'generation_dialogue',
 'document_policy_extraction': 'information_extraction',
 'document_procedure_extraction': 'information_extraction',
 'document_program_explanation': 'generation_dialogue',
 'document_structure_interpretation': 'document_perception',
 'document_summarization': 'generation_dialogue',
 'document_technical_explanation': 'generation_dialogue',
 'economic_law': 'financial_knowledge',
 'economics_and_monetary_policy': 'market_macro_reasoning',
 'entity_extraction_classification': 'information_extraction',
 'equity_price_driver_inference': 'market_macro_reasoning',
 'equity_valuation_interpretation': 'accounting_valuation',
 'esg_investment_reasoning': 'risk_policy_advice',
 'esg_issue_identification': 'risk_policy_advice',
 'ethical_decision_reasoning': 'risk_policy_advice',
 'evidence_retrieval': 'retrieval_grounding',
 'explanation_anomaly_causality': 'market_macro_reasoning',
 'finance': 'financial_knowledge',
 'financial_accounting': 'accounting_valuation',
 'financial_asset_management': 'financial_knowledge',
 'financial_asset_valuation': 'accounting_valuation',
 'financial_audit_and_controls': 'accounting_valuation',
 'financial_audit_fundamentals': 'accounting_valuation',
 'financial_business_management': 'financial_knowledge',
 'financial_calculation_reasoning': 'accounting_valuation',
 'financial_cash_flow_calculation': 'accounting_valuation',
 'financial_causal_event_reasoning': 'market_macro_reasoning',
 'financial_certification_exam_qa': 'financial_knowledge',
 'financial_certification_qa': 'financial_knowledge',
 'financial_concept_explanation': 'financial_knowledge',
 'financial_counterfactual_inference': 'market_macro_reasoning',
 'financial_consistency_error_detection': 'accounting_valuation',
 'financial_customer_analysis_and_marketing': 'financial_knowledge',
 'financial_customer_management': 'financial_knowledge',
 'financial_data_description': 'generation_dialogue',
 'financial_data_interpretation': 'financial_knowledge',
 'financial_data_ranking': 'financial_knowledge',
 'financial_definition_scope_reasoning': 'accounting_valuation',
 'financial_dialogue': 'generation_dialogue',
 'financial_diluted_eps_calculation': 'accounting_valuation',
 'financial_disclosure_evasion_detection': 'classification_sentiment',
 'financial_distress_score_calculation': 'accounting_valuation',
 'financial_document_title_classification': 'generation_dialogue',
 'financial_engineering': 'accounting_valuation',
 'financial_entity_extraction': 'information_extraction',
 'financial_event_extraction': 'information_extraction',
 'financial_evidence_reconciliation': 'retrieval_grounding',
 'financial_foundations': 'financial_knowledge',
 'financial_headline_classification': 'classification_sentiment',
 'financial_industry_classification': 'classification_sentiment',
 'financial_institution_governance': 'financial_knowledge',
 'financial_institution_operations': 'financial_knowledge',
 'financial_interest_rate_reasoning': 'accounting_valuation',
 'financial_liquidity_calculation': 'accounting_valuation',
 'financial_market_index_calculation': 'numerical_statistics',
 'financial_market_mechanism_reasoning': 'market_macro_reasoning',
 'financial_market_time_series_analysis': 'market_macro_reasoning',
 'financial_math_and_time_value': 'numerical_statistics',
 'financial_meeting_classification': 'classification_sentiment',
 'financial_metric_interpretation': 'financial_knowledge',
 'financial_multi_turn_perception': 'document_perception',
 'financial_numeric_labeling': 'classification_sentiment',
 'financial_numerical_reasoning': 'numerical_statistics',
 'financial_ocr': 'document_perception',
 'financial_per_share_calculation': 'accounting_valuation',
 'financial_planning_and_budgeting': 'financial_knowledge',
 'financial_professional_ethics': 'risk_policy_advice',
 'financial_question_decomposition': 'generation_dialogue',
 'financial_recapitalization_calculation': 'accounting_valuation',
 'financial_regulation_and_compliance': 'risk_policy_advice',
 'financial_relation_extraction': 'information_extraction',
 'financial_report_analysis': 'financial_knowledge',
 'financial_return_calculation': 'accounting_valuation',
 'financial_return_on_investment_calculation': 'accounting_valuation',
 'financial_risk_analysis': 'risk_policy_advice',
 'financial_semantic_role_labeling': 'information_extraction',
 'financial_sentiment_analysis': 'classification_sentiment',
 'financial_statement_adjustment_calculation': 'accounting_valuation',
 'financial_statement_calculation': 'accounting_valuation',
 'financial_summarization': 'generation_dialogue',
 'financial_system_and_institutions': 'financial_knowledge',
 'financial_technology_and_banking': 'financial_knowledge',
 'financial_term_explanation': 'financial_knowledge',
 'financial_time_reasoning': 'numerical_statistics',
 'financial_scenario_sensitivity_analysis': 'accounting_valuation',
 'financial_time_value_calculation': 'accounting_valuation',
 'financial_tool_use': 'financial_knowledge',
 'financial_topic_classification': 'classification_sentiment',
 'financial_translation': 'generation_dialogue',
 'financial_trust_management': 'financial_knowledge',
 'financial_truthfulness_qa': 'classification_sentiment',
 'financial_valuation_calculation': 'accounting_valuation',
 'financial_valuation_reasoning': 'accounting_valuation',
 'fiscal_policy_scenario_classification': 'classification_sentiment',
 'fixed_income_valuation_reasoning': 'accounting_valuation',
 'foreign_currency_translation_calculation': 'accounting_valuation',
 'function_relationship_reasoning': 'numerical_statistics',
 'general_dialogue': 'generation_dialogue',
 'general_legal_reasoning': 'risk_policy_advice',
 'global_events_impact': 'market_macro_reasoning',
 'hierarchical_table_qa': 'table_reasoning',
 'hypothesis_testing_reasoning': 'numerical_statistics',
 'image_caption': 'document_perception',
 'insufficient_information_detection': 'retrieval_grounding',
 'inclusive_finance': 'financial_knowledge',
 'industry_analysis_and_competition': 'financial_knowledge',
 'industry_sentiment_extraction': 'classification_sentiment',
 'industry_trend_inference': 'market_macro_reasoning',
 'insurance_finance': 'risk_policy_advice',
 'international_finance_and_forex': 'financial_knowledge',
 'investment_advice_strategy': 'risk_policy_advice',
 'investment_and_market_knowledge': 'market_macro_reasoning',
 'investor_suitability_assessment': 'risk_policy_advice',
 'legal_evidence_reasoning': 'retrieval_grounding',
 'long': 'multipage_financial_reasoning',
 'long_context_citation_grounded_qa': 'multipage_financial_reasoning',
 'long_document_cross_page': 'multipage_financial_reasoning',
 'macro_regime_classification': 'classification_sentiment',
 'macroeconomic_impact_inference': 'market_macro_reasoning',
 'macroeconomic_trend_inference': 'market_macro_reasoning',
 'management_accounting_and_budgeting': 'accounting_valuation',
 'management_accounting_and_costing': 'accounting_valuation',
 'market_concentration_calculation': 'market_macro_reasoning',
 'market_event_impact_inference': 'market_macro_reasoning',
 'merger_acquisition_completeness_classification': 'classification_sentiment',
 'monetary_policy_stance_classification': 'classification_sentiment',
 'multi_span_extraction': 'information_extraction',
 'multi_step_numerical_reasoning': 'numerical_statistics',
 'multi_table_reasoning': 'table_reasoning',
 'multimodal_financial_knowledge': 'financial_knowledge',
 'multimodal_financial_chart_reasoning_v5': 'chart_reasoning',
 'multimodal_financial_knowledge_v5': 'financial_knowledge',
 'news_title_generation': 'generation_dialogue',
 'nonbank_financial_institutions': 'financial_knowledge',
 'pattern_relationship_reasoning': 'numerical_statistics',
 'payroll_calculation': 'accounting_valuation',
 'personal_financial_planning': 'risk_policy_advice',
 'portfolio_allocation_risk_return': 'risk_policy_advice',
 'portfolio_and_risk_management': 'risk_policy_advice',
 'portfolio_performance_metric_calculation': 'accounting_valuation',
 'probability_expected_value_calculation': 'numerical_statistics',
 'probability_reasoning': 'numerical_statistics',
 'product_information_qa': 'financial_knowledge',
 'public_law_reasoning': 'risk_policy_advice',
 'python_programming': 'general_capability',
 'real_estate_finance_and_valuation': 'accounting_valuation',
 'relationship_equity_structure': 'information_extraction',
 'research_report_opinion_qa': 'financial_knowledge',
 'research_report_title_generation': 'generation_dialogue',
 'risk_sentiment_policy': 'risk_policy_advice',
 'schedule_temporal_reasoning': 'numerical_statistics',
 'single_table_qa': 'table_reasoning',
 'spatial_localization': 'document_perception',
 'statistical_hypothesis_testing': 'numerical_statistics',
 'statistical_inference_reasoning': 'numerical_statistics',
 'statistical_interval_estimation': 'numerical_statistics',
 'statistical_numerical_reasoning': 'numerical_statistics',
 'statistics': 'numerical_statistics',
 'statistics_comparison_ranking': 'numerical_statistics',
 'stock_movement_prediction': 'market_macro_reasoning',
 'summary_announcement': 'generation_dialogue',
 'supply_demand_reasoning': 'market_macro_reasoning',
 'sustainable_finance': 'risk_policy_advice',
 'table_aggregation_reasoning': 'table_reasoning',
 'table_arithmetic_reasoning': 'table_reasoning',
 'table_budget_decision': 'table_reasoning',
 'table_budget_reasoning': 'table_reasoning',
 'table_comparison_reasoning': 'table_reasoning',
 'table_counting': 'table_reasoning',
 'table_data_extraction': 'table_reasoning',
 'table_decision_reasoning': 'table_reasoning',
 'table_financial_arithmetic': 'table_reasoning',
 'table_math_reasoning': 'table_reasoning',
 'table_multi_hop_reasoning': 'table_reasoning',
 'table_multi_step_decision_reasoning': 'table_reasoning',
 'table_probability_reasoning': 'table_reasoning',
 'table_proportion_reasoning': 'table_reasoning',
 'table_rate_change': 'table_reasoning',
 'table_ratio_reasoning': 'table_reasoning',
 'table_statement_verification': 'table_reasoning',
 'table_statistical_reasoning': 'table_reasoning',
 'table_statistics_and_comparison': 'table_reasoning',
 'table_structure_detection': 'document_perception',
 'taxation_and_tax_law': 'risk_policy_advice',
 'temporal_financial_reasoning': 'numerical_statistics',
 'time_series_forecasting': 'market_macro_reasoning',
 'time_series_regression_forecasting': 'market_macro_reasoning',
 'trust_and_asset_management': 'financial_knowledge',
 'visual_counting': 'document_perception',
 'visual_pattern_reasoning': 'document_perception',
 'valuation_reasoning': 'accounting_valuation',
 'vligabench_ru': 'general_capability'}
FAMILY_CAP = {'accounting_valuation': 0.18,
 'chart_reasoning': 0.15,
 'classification_sentiment': 0.08,
 'document_perception': 0.10,
 'financial_knowledge': 0.2,
 'general_capability': 0.03,
 'generation_dialogue': 0.09,
 'information_extraction': 0.12,
 'market_macro_reasoning': 0.18,
 'multipage_financial_reasoning': 0.14,
 'numerical_statistics': 0.18,
 'retrieval_grounding': 0.13,
 'risk_policy_advice': 0.12,
 'table_reasoning': 0.15}
MAX_TASK_RATIO = 0.05
SMALL_TASK_MIN_N = 100
SMALL_TASK_MAX_N = 499
SMALL_TASK_RATIO = 0.02
PRIORITY_SMALL_TASK_RATIO = 0.04
TINY_TASK_MAX_N = 100
TINY_POOL_RATIO = 0.005
TINY_MAX_REPEAT = 2
UNKNOWN_TASK = "__unknown__"
_TINY_POOL_KEY = "__tiny_pool__"


def task_b_weight(task: str, modality: str) -> float:
    if modality == "multi":
        return MULTI_UPWEIGHT.get(task, 1.0) * MULTI_DOWNWEIGHT.get(task, 1.0)
    if modality == "text":
        return TEXT_UPWEIGHT.get(task, 1.0) * TEXT_DOWNWEIGHT.get(task, 1.0)
    raise ValueError(f"unknown modality: {modality}")


def task_length_scale(mean_assistant_tokens: float) -> float:
    return max(mean_assistant_tokens, MIN_ASSISTANT_TOKENS_FOR_WEIGHT) ** TOKEN_LENGTH_BETA


def family_for_task(task: str) -> str:
    return TASK_TO_FAMILY.get(task, task)


def alpha_for_step(step: int) -> float:
    for start, end, alpha in ALPHA_SCHEDULE:
        if start <= step < end:
            return alpha
    raise ValueError(f"step {step} outside alpha schedule")


def scan_task_index(path: Path) -> tuple[dict[str, list[int]], int]:
    task_index: dict[str, list[int]] = {}
    total = 0
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle):
            row = json.loads(line)
            task = str(row.get("task") or UNKNOWN_TASK)
            task_index.setdefault(task, []).append(line_no)
            total += 1
    return task_index, total


def _load_training_template(model: str, model_type: str, max_length: int):
    from swift.model import get_model_processor
    from swift.template import get_template

    _, processor = get_model_processor(model, model_type=model_type, load_model=False)
    # ms-swift represents the SFT `delete` strategy as template-level `raise`;
    # scan_encoded_index drops the resulting MaxLengthError rows.
    template = get_template(
        processor,
        max_length=max_length,
        truncation_strategy="raise",
        loss_scale="default",
    )
    template.set_mode("train")
    return template


def _token_counts(template, row: dict[str, Any]) -> tuple[int, int]:
    encoded = template.encode(row)
    if isinstance(encoded, list):
        raise ValueError("truncation produced multiple encoded rows")
    input_ids = encoded.get("input_ids")
    if input_ids is None:
        effective_token_count = 0
    else:
        if hasattr(input_ids, "reshape"):
            input_ids = input_ids.reshape(-1)
        if hasattr(input_ids, "tolist"):
            input_ids = input_ids.tolist()
        input_values = input_ids if isinstance(input_ids, list) else [input_ids]
        while input_values and isinstance(input_values[0], list):
            input_values = [item for nested in input_values for item in nested]
        effective_token_count = len(input_values)
    labels = encoded.get("labels")
    if labels is None:
        return 0, effective_token_count
    if hasattr(labels, "reshape"):
        labels = labels.reshape(-1)
    if hasattr(labels, "tolist"):
        labels = labels.tolist()
    values = labels if isinstance(labels, list) else [labels]
    while values and isinstance(values[0], list):
        values = [item for nested in values for item in nested]
    return sum(int(value != -100) for value in values), effective_token_count


def _shard_offsets(path: Path, num_proc: int) -> list[tuple[int, int, int]]:
    """Return (start_byte, line_count, raw_start) shards covering all lines in order."""
    offsets: list[int] = [0]
    with path.open("rb") as handle:
        while handle.readline():
            offsets.append(handle.tell())
    n_lines = len(offsets) - 1
    shards: list[tuple[int, int, int]] = []
    base = 0
    for i in range(num_proc):
        count = (n_lines - base) // (num_proc - i)
        shards.append((offsets[base], count, base))
        base += count
    return shards


def _scan_shard_worker(args: tuple) -> tuple[int, list[tuple[int, str, int, int, str]]]:
    path, start_offset, count, raw_start, model, model_type, max_length = args
    template = _load_training_template(model, model_type, max_length) if model else None
    records: list[tuple[int, str, int, int, str]] = []
    nonempty = 0
    with open(path, "rb") as handle:
        handle.seek(start_offset)
        for offset_index in range(count):
            raw = handle.readline().decode("utf-8")
            if not raw:
                break
            if not raw.strip():
                continue
            nonempty += 1
            raw_index = raw_start + offset_index
            row = json.loads(raw)
            task = str(row.get("task") or UNKNOWN_TASK)
            if template is None:
                records.append((raw_index, task, 1, 1, "ok"))
                continue
            try:
                token_count, effective_token_count = _token_counts(template, row)
                records.append((raw_index, task, int(token_count), int(effective_token_count), "ok"))
            except Exception as exc:
                try:
                    from swift.template import MaxLengthError
                except ImportError:
                    MaxLengthError = ()
                if MaxLengthError and isinstance(exc, MaxLengthError):
                    records.append((raw_index, task, 0, 0, "maxlen"))
                else:
                    records.append((raw_index, task, 0, 0, "failed"))
    return nonempty, records


def _sub_shard_offsets(path: Path, start_offset: int, count: int, raw_start: int, num_proc: int) -> list[tuple[int, int, int]]:
    """Split a line range [start_offset, count) into num_proc contiguous sub-shards."""
    offsets: list[int] = []
    with open(path, "rb") as handle:
        handle.seek(start_offset)
        for _ in range(count):
            offsets.append(handle.tell())
            handle.readline()
        offsets.append(handle.tell())
    shards: list[tuple[int, int, int]] = []
    base = 0
    for i in range(num_proc):
        n = (count - base) // (num_proc - i)
        shards.append((offsets[base], n, raw_start + base))
        base += n
    return shards


def _scan_range(
    path: Path,
    start_offset: int,
    count: int,
    raw_start: int,
    *,
    model: str | None,
    model_type: str,
    max_length: int,
    num_proc: int,
) -> tuple[int, list[tuple[int, str, int, int, str]]]:
    if num_proc <= 1:
        return _scan_shard_worker((str(path), start_offset, count, raw_start, model, model_type, max_length))
    shard_args = [
        (str(path), start, n, rs, model, model_type, max_length)
        for start, n, rs in _sub_shard_offsets(path, start_offset, count, raw_start, num_proc)
    ]
    with multiprocessing.Pool(num_proc) as pool:
        results = pool.map(_scan_shard_worker, shard_args)
    nonempty = 0
    records: list[tuple[int, str, int, int, str]] = []
    for n, shard_records in results:
        nonempty += n
        records.extend(shard_records)
    return nonempty, records


def _scan_node_partials(
    path: Path,
    *,
    modality: str,
    node_rank: int,
    node_count: int,
    model: str | None,
    model_type: str,
    max_length: int,
    num_proc: int,
    output_dir: Path,
    wait_timeout: int,
) -> tuple[int, list[tuple[int, str, int, int, str]]]:
    """Scan this node's line range, write a partial file; node 0 merges all partials."""
    output_dir.mkdir(parents=True, exist_ok=True)
    node_shards = _shard_offsets(path, node_count)
    start, count, raw_start = node_shards[node_rank]
    nonempty, records = _scan_range(
        path, start, count, raw_start,
        model=model, model_type=model_type, max_length=max_length, num_proc=num_proc,
    )
    partial = output_dir / f"partial_{modality}.rank{node_rank:04d}.jsonl"
    with partial.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    if node_rank != 0:
        return nonempty, []
    deadline = time.monotonic() + wait_timeout
    while True:
        missing = [
            rank for rank in range(node_count)
            if not (output_dir / f"partial_{modality}.rank{rank:04d}.jsonl").is_file()
        ]
        if not missing:
            break
        if time.monotonic() >= deadline:
            raise RuntimeError(f"timed out waiting for scan partials: {missing} ({path})")
        time.sleep(2)
    merged: list[tuple[int, str, int, int, str]] = []
    for rank in range(node_count):
        with (output_dir / f"partial_{modality}.rank{rank:04d}.jsonl").open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    merged.append(tuple(json.loads(line)))
    return len(merged), merged


def _record_to_index(
    stats: dict[str, int],
    task_index: dict[str, list[dict[str, Any]]],
    cache_rows: list[dict[str, Any]],
    *,
    modality: str,
    raw_index: int,
    task: str,
    token_count: int,
    effective_token_count: int,
    kind: str,
) -> None:
    if kind == "maxlen":
        stats["deleted"] += 1
        return
    if kind == "failed":
        stats["encoding_failed"] += 1
        return
    dataset_index = stats["retained"]
    stats["retained"] += 1
    family = family_for_task(task)
    cache_rows.append(
        {
            "modality": modality,
            "dataset_index": dataset_index,
            "raw_index": raw_index,
            "task": task,
            "family": family,
            "assistant_token_count": int(token_count),
            "effective_token_count": int(effective_token_count),
            "eligible": bool(token_count > 0),
        }
    )
    if token_count <= 0:
        stats["zero_supervision"] += 1
        return
    stats["eligible"] += 1
    task_index.setdefault(task, []).append(
        {
            "index": dataset_index,
            "raw_index": raw_index,
            "task": task,
            "family": family,
            "assistant_token_count": int(token_count),
            "effective_token_count": int(effective_token_count),
        }
    )


def scan_encoded_index(
    path: Path,
    *,
    modality: str,
    model: str | None,
    model_type: str = "qwen3_vl",
    max_length: int = 49152,
    num_proc: int = 1,
    node_rank: int = 0,
    node_count: int = 1,
    output_dir: Path | None = None,
    wait_timeout: int = 1800,
) -> tuple[dict[str, list[dict[str, Any]]], int, int, list[dict[str, Any]], dict[str, int]]:
    stats = {"raw": 0, "retained": 0, "eligible": 0, "deleted": 0, "encoding_failed": 0, "zero_supervision": 0}
    task_index: dict[str, list[dict[str, Any]]] = {}
    cache_rows: list[dict[str, Any]] = []

    def records() -> Iterator[tuple[int, str, int, int, str]]:
        if node_count > 1:
            _nonempty, node_records = _scan_node_partials(
                path,
                modality=modality,
                node_rank=node_rank,
                node_count=node_count,
                model=model,
                model_type=model_type,
                max_length=max_length,
                num_proc=num_proc,
                output_dir=output_dir,
                wait_timeout=wait_timeout,
            )
            yield from node_records
            return
        if num_proc <= 1:
            template = _load_training_template(model, model_type, max_length) if model else None
            with path.open(encoding="utf-8") as handle:
                for raw_index, line in enumerate(handle):
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    task = str(row.get("task") or UNKNOWN_TASK)
                    if template is None:
                        yield raw_index, task, 1, 1, "ok"
                        continue
                    try:
                        token_count, effective_token_count = _token_counts(template, row)
                        yield raw_index, task, int(token_count), int(effective_token_count), "ok"
                    except Exception as exc:
                        try:
                            from swift.template import MaxLengthError
                        except ImportError:
                            MaxLengthError = ()
                        if MaxLengthError and isinstance(exc, MaxLengthError):
                            yield raw_index, task, 0, 0, "maxlen"
                        else:
                            yield raw_index, task, 0, 0, "failed"
        else:
            shard_args = [
                (str(path), start, count, raw_start, model, model_type, max_length)
                for start, count, raw_start in _shard_offsets(path, num_proc)
            ]
            with multiprocessing.Pool(num_proc) as pool:
                results = pool.map(_scan_shard_worker, shard_args)
            for _nonempty, shard_records in results:
                yield from shard_records

    for raw_index, task, token_count, effective_token_count, kind in records():
        stats["raw"] += 1
        _record_to_index(
            stats,
            task_index,
            cache_rows,
            modality=modality,
            raw_index=raw_index,
            task=task,
            token_count=token_count,
            effective_token_count=effective_token_count,
            kind=kind,
        )
    return task_index, stats["retained"], stats["eligible"], cache_rows, stats


def task_cap(task: str, count: int, quota: int) -> int:
    if count < TINY_TASK_MAX_N:
        return max(1, int(quota * TINY_POOL_RATIO))
    if SMALL_TASK_MIN_N <= count <= SMALL_TASK_MAX_N:
        ratio = PRIORITY_SMALL_TASK_RATIO if task in PRIORITY_SMALL_TASKS else SMALL_TASK_RATIO
    else:
        ratio = MAX_TASK_RATIO
    return max(1, int(quota * ratio))


def allocate_quotas(
    counts: dict[str, int],
    quota: int,
    alpha: float,
    modality: str,
    means: dict[str, float] | None = None,
) -> tuple[dict[str, int], int, list[str]]:
    means = means or {task: 1.0 for task in counts}
    tiny_tasks = sorted(task for task, count in counts.items() if count < TINY_TASK_MAX_N)
    sampling_weights = {
        task: (count**alpha) * task_b_weight(task, modality) / task_length_scale(means[task])
        for task, count in counts.items()
        if task not in tiny_tasks
    }
    if tiny_tasks:
        sampling_weights[_TINY_POOL_KEY] = sum(
            (counts[task]**alpha) * task_b_weight(task, modality) / task_length_scale(means[task])
            for task in tiny_tasks
        )

    def cap_fn(task: str) -> int:
        if task == _TINY_POOL_KEY:
            return quota if not any(task_name not in tiny_tasks for task_name in counts) else max(1, int(quota * TINY_POOL_RATIO))
        return task_cap(task, counts[task], quota)

    pending = dict(sampling_weights)
    values: dict[str, float] = {}
    remaining = float(quota)
    for _ in range(len(pending) + 1):
        total = sum(pending.values())
        if total <= 0 or remaining <= 1e-9:
            break
        for task in list(pending):
            raw = remaining * pending[task] / total
            take = min(raw, cap_fn(task))
            values[task] = values.get(task, 0.0) + take
            if raw >= cap_fn(task) - 1e-9:
                del pending[task]
        remaining = quota - sum(values.values())
    floors = {task: int(value) for task, value in values.items()}
    deficit = quota - sum(floors.values())
    order = sorted(values, key=lambda task: (values[task] - int(values[task]), task), reverse=True)
    for task in order:
        if deficit <= 0:
            break
        if floors[task] < cap_fn(task):
            floors[task] += 1
            deficit -= 1
    if deficit > 0:
        raise ValueError(f"unable to allocate quota={quota}: task caps sum below quota")
    tiny_quota = int(floors.pop(_TINY_POOL_KEY, 0))
    return floors, tiny_quota, tiny_tasks


def sample_task_indices(indices: list[int], quota: int, rng: random.Random) -> list[int]:
    pool = list(indices)
    rng.shuffle(pool)
    if not pool or quota <= 0:
        return []
    result: list[int] = []
    while len(result) < quota:
        if not pool:
            pool = list(indices)
            rng.shuffle(pool)
        result.append(pool.pop())
    return result


class PersistentCursor:
    def __init__(self, seed: int):
        self.seed = seed
        self.states: dict[tuple[str, str], dict[str, Any]] = {}

    def _state(self, modality: str, task: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        key = (modality, task)
        state = self.states.get(key)
        if state is None:
            state = {"pool": list(entries), "cursor": 0, "pending": []}
            stable = sum((index + 1) * ord(char) for index, char in enumerate(f"{modality}:{task}"))
            random.Random(self.seed + stable).shuffle(state["pool"])
            self.states[key] = state
        return state

    def peek(self, modality: str, task: str, entries: list[dict[str, Any]]) -> dict[str, Any]:
        state = self._state(modality, task, entries)
        if state["pending"]:
            return state["pending"][0]
        if state["cursor"] >= len(state["pool"]):
            state["pool"] = list(entries)
            state["cursor"] = 0
            random.Random(self.seed + len(state["pool"]) + state.get("reshuffles", 0)).shuffle(state["pool"])
            state["reshuffles"] = state.get("reshuffles", 0) + 1
        return state["pool"][state["cursor"]]

    def draw(self, modality: str, task: str, entries: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
        state = self._state(modality, task, entries)
        picked = []
        for _ in range(count):
            if state["pending"]:
                picked.append(state["pending"].pop(0))
            else:
                picked.append(self.peek(modality, task, entries))
                state["cursor"] += 1
        return picked

    def put_back(self, modality: str, task: str, entries: list[dict[str, Any]], entry: dict[str, Any]) -> None:
        self._state(modality, task, entries)["pending"].insert(0, entry)


def _sample_tiny_pool(
    tiny_tasks: list[str],
    task_index: dict[str, list[dict[str, Any]]],
    quota: int,
    means: dict[str, float],
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    *,
    modality: str,
    alpha: float,
) -> list[dict[str, Any]]:
    picked: list[dict[str, Any]] = []
    all_tiny = bool(task_index) and len(tiny_tasks) == len(task_index)
    if all_tiny:
        while len(picked) < quota:
            tasks = sorted(tiny_tasks)
            weights = [
                len(task_index[task]) ** alpha
                    * task_b_weight(task, modality)
                / task_length_scale(means[task])
                for task in tasks
            ]
            task = rng.choices(tasks, weights=weights, k=1)[0]
            min_usage = min(
                usage.get((modality, entry["index"]), 0)
                for entry in task_index[task]
            )
            candidates = [
                entry for entry in task_index[task]
                if usage.get((modality, entry["index"]), 0) == min_usage
            ]
            entry = rng.choice(candidates)
            picked.append(entry)
            key = (modality, entry["index"])
            usage[key] = usage.get(key, 0) + 1
        return picked

    eligible = {
        task: [
            entry for entry in task_index[task]
            if usage.get((modality, entry["index"]), 0) < TINY_MAX_REPEAT
        ]
        for task in tiny_tasks
    }
    eligible = {task: rows for task, rows in eligible.items() if rows}
    while len(picked) < quota and eligible:
        tasks = sorted(eligible)
        weights = [len(task_index[task]) ** alpha * task_b_weight(task, modality) / task_length_scale(means[task]) for task in tasks]
        task = rng.choices(tasks, weights=weights, k=1)[0]
        entry = rng.choice(eligible[task])
        eligible[task].remove(entry)
        if not eligible[task]:
           del eligible[task]
        picked.append(entry)
    for entry in picked:
        key = (modality, entry["index"])
        usage[key] = usage.get(key, 0) + 1
    return picked


def sample_tiny_pool(
    tiny_tasks: list[str],
    task_index: dict[str, list[int]],
    quota: int,
    alpha: float,
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    *,
    modality: str,
) -> list[int]:
    rows = {
        task: [
            {
                "index": index,
                "raw_index": index,
                "task": task,
                "family": family_for_task(task),
                "assistant_token_count": 1,
            }
            for index in indices
        ]
        for task, indices in task_index.items()
    }
    result = _sample_tiny_pool(
        tiny_tasks, rows, quota, {task: 1.0 for task in tiny_tasks}, usage, rng,
        modality=modality, alpha=alpha,
    )
    return [entry["index"] for entry in result]


def _distribution(samples: list[dict[str, Any]]) -> dict[str, Any]:
    tasks: dict[str, dict[str, int]] = {}
    families: dict[str, dict[str, int]] = {}
    for entry in samples:
        assistant_tokens = int(entry["assistant_token_count"])
        effective_tokens = int(entry.get("effective_token_count", assistant_tokens))
        task = entry["task"]
        family = entry["family"]
        tasks.setdefault(task, {"samples": 0, "assistant_tokens": 0, "effective_tokens": 0})
        families.setdefault(family, {"samples": 0, "assistant_tokens": 0, "effective_tokens": 0})
        tasks[task]["samples"] += 1
        tasks[task]["assistant_tokens"] += assistant_tokens
        tasks[task]["effective_tokens"] += effective_tokens
        families[family]["samples"] += 1
        families[family]["assistant_tokens"] += assistant_tokens
        families[family]["effective_tokens"] += effective_tokens
    total_samples = len(samples)
    total_assistant_tokens = sum(v["assistant_tokens"] for v in tasks.values())
    total_effective_tokens = sum(v["effective_tokens"] for v in tasks.values())
    for grouped in (tasks, families):
        for values in grouped.values():
            values["sample_ratio"] = values["samples"] / total_samples if total_samples else 0.0
            values["token_ratio"] = values["assistant_tokens"] / total_assistant_tokens if total_assistant_tokens else 0.0
            values["effective_token_ratio"] = (
                values["effective_tokens"] / total_effective_tokens if total_effective_tokens else 0.0
            )
    return {
        "samples": total_samples,
        "assistant_tokens": total_assistant_tokens,
        "effective_tokens": total_effective_tokens,
        "sample_ratio": 1.0 if total_samples else 0.0,
        "token_ratio": 1.0 if total_assistant_tokens else 0.0,
        "effective_token_ratio": 1.0 if total_effective_tokens else 0.0,
        "tasks": tasks,
        "families": families,
    }


def _family_violation(samples: list[dict[str, Any]]) -> tuple[str | None, float, float]:
    total = sum(int(entry["assistant_token_count"]) for entry in samples)
    if total <= 0:
        return None, 0.0, 0.0
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in samples:
        grouped.setdefault(entry["family"], []).append(entry)
    violations = []
    for family, rows in grouped.items():
        cap = FAMILY_CAP.get(family)
        if cap is None:
            continue
        tokens = sum(int(row["assistant_token_count"]) for row in rows)
        excess = tokens - cap * total
        tolerance = max(int(row["assistant_token_count"]) for row in rows)
        if excess > tolerance:
            violations.append((excess, family, tolerance))
    if not violations:
        return None, 0.0, 0.0
    excess, family, tolerance = max(violations, key=lambda value: (value[0], value[1]))
    return family, excess, tolerance


def _repair_family_caps(
    samples: list[dict[str, Any]],
    task_index: dict[str, list[dict[str, Any]]],
    quotas: dict[str, int],
    tiny_tasks: set[str],
    tiny_quota: int,
    cursor: PersistentCursor,
    *,
    modality: str,
    usage: dict[tuple[str, int], int],
) -> list[dict[str, Any]]:
    selected = collections.Counter((entry["index"], entry["task"]) for entry in samples)
    allow_tiny_reuse = bool(task_index) and len(tiny_tasks) == len(task_index)
    while True:
        family, excess, tolerance = _family_violation(samples)
        if family is None:
            return samples

        total_tokens = sum(int(row["assistant_token_count"]) for row in samples)
        family_rows = [row for row in samples if row["family"] == family]
        family_tokens = sum(int(row["assistant_token_count"]) for row in family_rows)
        cap_ratio = FAMILY_CAP[family]

        family_token_totals: dict[str, int] = {}
        family_max_token: dict[str, int] = {}
        for row in samples:
            row_family = row["family"]
            row_tokens = int(row["assistant_token_count"])
            family_token_totals[row_family] = family_token_totals.get(row_family, 0) + row_tokens
            family_max_token[row_family] = max(family_max_token.get(row_family, 0), row_tokens)

        best: tuple[float, str, int, dict[str, Any], dict[str, Any]] | None = None

        for old_pool in (False, True):
            old_candidates = [row for row in family_rows if (row["task"] in tiny_tasks) == old_pool]
            if not old_candidates:
                continue

            old = min(
                old_candidates,
                key=lambda row: (-int(row["assistant_token_count"]), row["task"], int(row["index"])),
            )
            old_tokens = int(old["assistant_token_count"])

            for task in sorted(task_index):
                if (task in tiny_tasks) != old_pool:
                    continue
                if family_for_task(task) == family:
                    continue

                cap = tiny_quota if old_pool else task_cap(task, len(task_index[task]), len(samples))
                if quotas.get(task, 0) >= cap:
                    continue

                if old_pool:
                    rows = [
                        row for row in task_index[task]
                        if allow_tiny_reuse
                        or (
                            usage.get((modality, row["index"]), 0) < TINY_MAX_REPEAT
                            and selected[(row["index"], row["task"])] == 0
                        )
                    ]
                    if not rows:
                        continue
                    candidate = min(
                        rows,
                        key=lambda row: (int(row["assistant_token_count"]), row["task"], int(row["index"])),
                    )
                else:
                    candidate = cursor.peek(modality, task, task_index[task])
                    if selected[(candidate["index"], candidate["task"])] > 0:
                        continue

                candidate_tokens = int(candidate["assistant_token_count"])
                new_total = total_tokens - old_tokens + candidate_tokens
                new_family_tokens = family_tokens - old_tokens
                new_excess = new_family_tokens - cap_ratio * new_total
                score = excess - max(0.0, new_excess)
                if score <= 0:
                    continue

                dst_family = candidate["family"]
                dst_cap = FAMILY_CAP.get(dst_family)
                if dst_cap is not None:
                    dst_tokens = family_token_totals.get(dst_family, 0) + candidate_tokens
                    dst_tolerance = max(family_max_token.get(dst_family, 0), candidate_tokens)
                    if dst_tokens - dst_cap * new_total > dst_tolerance:
                        continue

                item = (score, task, int(candidate["index"]), old, candidate)
                if best is None or item[0] > best[0] or (
                    item[0] == best[0] and (item[1], item[2]) < (best[1], best[2])
                ):
                    best = item

        if best is None:
            if excess <= tolerance:
                return samples
            raise ValueError(f"family cap cannot be satisfied for family={family}")

        _, _, _, old, candidate = best
        if candidate["task"] in tiny_tasks:
            candidate = dict(candidate, tiny_pool=True)

        samples[samples.index(old)] = candidate
        if old["task"] not in tiny_tasks:
            quotas[old["task"]] = quotas.get(old["task"], 0) - 1
            quotas[candidate["task"]] = quotas.get(candidate["task"], 0) + 1
        selected[(old["index"], old["task"])] -= 1
        selected[(candidate["index"], candidate["task"])] += 1

        if old["task"] in tiny_tasks:
            old_key = (modality, old["index"])
            usage[old_key] = max(0, usage.get(old_key, 0) - 1)
        if candidate["task"] in tiny_tasks:
            candidate_key = (modality, candidate["index"])
            usage[candidate_key] = usage.get(candidate_key, 0) + 1

        if candidate["task"] not in tiny_tasks:
            cursor.draw(modality, candidate["task"], task_index[candidate["task"]], 1)
            cursor.put_back(modality, old["task"], task_index[old["task"]], old)



def _sample_modality(
    task_index: dict[str, list[dict[str, Any]]],
    quota: int,
    alpha: float,
    means: dict[str, float],
    usage: dict[tuple[str, int], int],
    rng: random.Random,
    cursor: PersistentCursor,
    *,
    modality: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    counts = {task: len(rows) for task, rows in task_index.items()}
    allocations, tiny_quota, tiny_tasks = allocate_quotas(counts, quota, alpha, modality, means)
    samples: list[dict[str, Any]] = []
    for task in sorted(allocations):
        samples.extend(cursor.draw(modality, task, task_index[task], allocations[task]))
    tiny_samples = _sample_tiny_pool(
        tiny_tasks, task_index, tiny_quota, means, usage, rng, modality=modality, alpha=alpha
    )
    tiny_samples = [dict(row, tiny_pool=True) for row in tiny_samples]
    samples.extend(tiny_samples)
    quotas = dict(allocations)
    quotas[_TINY_POOL_KEY] = tiny_quota
    shortfall = quota - len(samples)
    if shortfall > 0:
        capacities = {
            task: max(0, task_cap(task, counts[task], quota) - allocations[task])
            for task in allocations
        }
        pending = {
            task: counts[task] ** alpha * task_b_weight(task, modality) / task_length_scale(means[task])
            for task, capacity in capacities.items()
            if capacity > 0
        }
        while shortfall > 0 and pending:
            total = sum(pending.values())
            if total <= 0:
                break
            for task in list(pending):
                if shortfall <= 0:
                    break
                take = min(
                    capacities[task],
                    shortfall,
                    max(1, int(shortfall * pending[task] / total)),
                )
                samples.extend(cursor.draw(modality, task, task_index[task], take))
                quotas[task] = quotas.get(task, 0) + take
                capacities[task] -= take
                shortfall -= take
                if capacities[task] <= 0:
                    del pending[task]
        if shortfall > 0:
            raise ValueError(f"cannot cover tiny shortfall {shortfall}")
    _repair_family_caps(
        samples,
        task_index,
        quotas,
        set(tiny_tasks),
        tiny_quota,
        cursor,
        modality=modality,
        usage=usage,
    )
    rng.shuffle(samples)
    return samples, quotas


def _split_uneven(count: int, parts: int) -> list[int]:
    base, extra = divmod(count, parts)
    return [base + 1 if index < extra else base for index in range(parts)]


def build_block(
    *,
    block_id: int,
    start_step: int,
    steps: int,
    global_batch_size: int,
    dp_world_size: int,
    per_device_batch: int,
    grad_acc: int,
    seed: int,
    multi_ratio: float = DEFAULT_MULTI_RATIO,
    multi_index: dict[str, list[dict[str, Any]]] | dict[str, list[int]],
    text_index: dict[str, list[dict[str, Any]]] | dict[str, list[int]],
    tiny_usage: dict[tuple[str, int], int],
    cursor: PersistentCursor | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[tuple[str, int], int]]:
    rng = random.Random(seed * 100_000 + block_id)
    cursor = cursor or PersistentCursor(seed * 100_000)
    alpha = alpha_for_step(start_step)
    def normalize(index: dict[str, list[Any]], modality: str) -> dict[str, list[dict[str, Any]]]:
        return {
            task: [
                row if isinstance(row, dict) else {
                    "index": int(row),
                    "raw_index": int(row),
                    "task": task,
                    "family": family_for_task(task),
                    "assistant_token_count": 1,
                    "effective_token_count": 1,
                }
                for row in rows
            ]
            for task, rows in index.items()
        }
    multi_index = normalize(multi_index, "multi")
    text_index = normalize(text_index, "text")
    multi_quota = int(steps * global_batch_size * multi_ratio + 0.5)
    text_quota = steps * global_batch_size - multi_quota
    multi_means = {task: sum(row["assistant_token_count"] for row in rows) / len(rows) for task, rows in multi_index.items()}
    text_means = {task: sum(row["assistant_token_count"] for row in rows) / len(rows) for task, rows in text_index.items()}
    multi_samples, multi_quotas = _sample_modality(multi_index, multi_quota, alpha, multi_means, tiny_usage, rng, cursor, modality="multi")
    text_samples, text_quotas = _sample_modality(text_index, text_quota, alpha, text_means, tiny_usage, rng, cursor, modality="text")
    multi_effective_tokens = sum(int(row.get("effective_token_count", row["assistant_token_count"])) for row in multi_samples)
    text_effective_tokens = sum(int(row.get("effective_token_count", row["assistant_token_count"])) for row in text_samples)
    effective_total = multi_effective_tokens + text_effective_tokens
    multi_effective_token_ratio = multi_effective_tokens / effective_total if effective_total else 0.0
    if multi_effective_token_ratio > MAX_MULTI_EFFECTIVE_TOKEN_RATIO:
        raise ValueError(
            f"multimodal effective-token ratio {multi_effective_token_ratio:.4f} exceeds hard cap "
            f"{MAX_MULTI_EFFECTIVE_TOKEN_RATIO:.2f}; reduce --multi-ratio"
        )
    micro_steps = steps * grad_acc
    per_micro = dp_world_size * per_device_batch
    # 长度感知组步：同步训练中微步耗时由组内最长样本决定。
    # 按 effective_token_count 降序后每 per_micro 条一组，长样本集中且组内长度相近，
    # 最小化所有微步最长样本之和（即总步时），同时不丢弃任何样本。
    combined = [(row, "multi") for row in multi_samples] + [(row, "text") for row in text_samples]
    combined.sort(
        key=lambda item: int(item[0].get("effective_token_count", item[0]["assistant_token_count"])),
        reverse=True,
    )
    entries: list[dict[str, Any]] = []
    for micro_index in range(micro_steps):
        chunk = combined[micro_index * per_micro:(micro_index + 1) * per_micro]
        for position, (row, modality) in enumerate(chunk):
            entries.append({
                "block": block_id,
                "micro_step": start_step * grad_acc + micro_index,
                "position_in_micro_step": position,
                "modality": modality,
                "task": row["task"],
                "family": row["family"],
                "index": row["index"],
                "raw_index": row.get("raw_index", row["index"]),
                "assistant_token_count": int(row["assistant_token_count"]),
                "effective_token_count": int(row.get("effective_token_count", row["assistant_token_count"])),
                "tiny_pool": bool(row.get("tiny_pool", False)),
                "pool": _TINY_POOL_KEY if row.get("tiny_pool", False) else "regular",
            })
    block_info = {
        "block_id": block_id,
        "start_step": start_step,
        "steps": steps,
        "alpha": alpha,
        "multi_effective_token_ratio": multi_effective_token_ratio,
        "quotas": {"multi": multi_quotas, "text": text_quotas},
        "planned": {
            "multi": _distribution([entry for entry in entries if entry["modality"] == "multi"]),
            "text": _distribution([entry for entry in entries if entry["modality"] == "text"]),
        },
    }
    return entries, block_info, tiny_usage


def generate_plan(
    *,
    train_multi: Path,
    train_text: Path,
    output_dir: Path,
    global_batch_size: int,
    dp_world_size: int,
    per_device_batch: int = 1,
    grad_acc: int,
    seed: int,
    multi_ratio: float = DEFAULT_MULTI_RATIO,
    max_steps: int | None = None,
    epochs: int = 1,
    steps_per_block: int = 200,
    model: str | None = None,
    model_type: str = "qwen3_vl",
    max_length: int = 49152,
    scan_num_proc: int = 1,
    node_rank: int = 0,
    node_count: int = 1,
    partial_wait_timeout: int = 1800,
) -> dict[str, Any]:
    if not 0.0 < multi_ratio < 1.0:
        raise ValueError(f"multi_ratio must be between 0 and 1, got {multi_ratio}")
    if global_batch_size != dp_world_size * per_device_batch * grad_acc:
        raise ValueError("global_batch_size must equal dp_world_size * per_device_batch * grad_acc")
    if per_device_batch != 1:
        raise ValueError("sample plan actual accounting requires per_device_batch=1")
    output_dir.mkdir(parents=True, exist_ok=True)
    multi_index, dataset_n_multi, eligible_n_multi, multi_cache, multi_stats = scan_encoded_index(
        train_multi,
        modality="multi",
        model=model,
        model_type=model_type,
        max_length=max_length,
        num_proc=scan_num_proc,
        node_rank=node_rank,
        node_count=node_count,
        output_dir=output_dir,
        wait_timeout=partial_wait_timeout,
    )
    text_index, dataset_n_text, eligible_n_text, text_cache, text_stats = scan_encoded_index(
        train_text,
        modality="text",
        model=model,
        model_type=model_type,
        max_length=max_length,
        num_proc=scan_num_proc,
        node_rank=node_rank,
        node_count=node_count,
        output_dir=output_dir,
        wait_timeout=partial_wait_timeout,
    )
    (output_dir / "token_cache_multi.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in multi_cache), encoding="utf-8"
    )
    (output_dir / "token_cache_text.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in text_cache), encoding="utf-8"
    )
    if max_steps is None:
        max_steps = (5 * eligible_n_multi + eligible_n_text) * epochs // global_batch_size
    total_blocks = (max_steps + steps_per_block - 1) // steps_per_block
    tiny_usage: dict[tuple[str, int], int] = {}
    cursor = PersistentCursor(seed * 100_000)
    blocks: list[dict[str, Any]] = []
    for block_id in range(total_blocks):
        start_step = block_id * steps_per_block
        steps = min(steps_per_block, max_steps - start_step)
        entries, block_info, tiny_usage = build_block(
            block_id=block_id, start_step=start_step, steps=steps,
            global_batch_size=global_batch_size, dp_world_size=dp_world_size,
            per_device_batch=per_device_batch, grad_acc=grad_acc, seed=seed,
            multi_ratio=multi_ratio, multi_index=multi_index, text_index=text_index,
            tiny_usage=tiny_usage, cursor=cursor,
        )
        with (output_dir / f"block_{block_id:04d}.jsonl").open("w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        blocks.append(block_info)
    meta = {
        "max_steps": max_steps, "total_blocks": total_blocks, "steps_per_block": steps_per_block,
        "N_multi": dataset_n_multi, "N_text": dataset_n_text,
        "eligible_N_multi": eligible_n_multi, "eligible_N_text": eligible_n_text,
        "dataset_stats": {"multi": multi_stats, "text": text_stats},
        "global_batch_size": global_batch_size, "dp_world_size": dp_world_size,
        "per_device_batch": per_device_batch, "grad_acc": grad_acc, "seed": seed,
        "epochs": epochs, "multi_ratio": multi_ratio, "text_ratio": 1.0 - multi_ratio,
        "model": model, "model_type": model_type, "max_length": max_length,
        "truncation_strategy": "delete",
        "image_max_token_num": os.environ.get("IMAGE_MAX_TOKEN_NUM", "512"),
        "family_cap": FAMILY_CAP, "blocks": blocks,
        "tiny_usage": {f"{modality}:{index}": count for (modality, index), count in tiny_usage.items()},
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / ".ready").write_text("ready\n", encoding="utf-8")
    return meta


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="generate deterministic SFT sampling plan")
    parser.add_argument("--train-multi", type=Path, required=True)
    parser.add_argument("--train-text", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--global-batch-size", type=int, default=24)
    parser.add_argument("--dp-world-size", type=int, default=12)
    parser.add_argument("--per-device-batch", type=int, default=1)
    parser.add_argument("--grad-acc", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--multi-ratio", type=float, default=DEFAULT_MULTI_RATIO)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--steps-per-block", type=int, default=200)
    parser.add_argument("--model", "--base-model", dest="model", type=str, default=None)
    parser.add_argument("--model-type", "--model_type", dest="model_type", type=str, default="qwen3_vl")
    parser.add_argument("--max-length", "--max_length", dest="max_length", type=int, default=49152)
    parser.add_argument("--scan-num-proc", "--scan_num_proc", dest="scan_num_proc", type=int, default=1)
    parser.add_argument("--node-rank", "--node_rank", dest="node_rank", type=int, default=0)
    parser.add_argument("--node-count", "--node_count", dest="node_count", type=int, default=1)
    parser.add_argument("--partial-wait-timeout", "--partial_wait_timeout", dest="partial_wait_timeout", type=int, default=1800)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.node_count > 1 and args.node_rank > 0:
        for path, modality in ((args.train_multi, "multi"), (args.train_text, "text")):
            _scan_node_partials(
                path,
                modality=modality,
                node_rank=args.node_rank,
                node_count=args.node_count,
                model=args.model,
                model_type=args.model_type,
                max_length=args.max_length,
                num_proc=args.scan_num_proc,
                output_dir=args.output_dir,
                wait_timeout=args.partial_wait_timeout,
            )
        print(f"node {args.node_rank}/{args.node_count} partial scan done", flush=True)
        return 0
    meta = generate_plan(
        train_multi=args.train_multi, train_text=args.train_text, output_dir=args.output_dir,
        global_batch_size=args.global_batch_size, dp_world_size=args.dp_world_size,
        per_device_batch=args.per_device_batch, grad_acc=args.grad_acc, seed=args.seed,
        multi_ratio=args.multi_ratio, max_steps=args.max_steps, epochs=args.epochs,
        steps_per_block=args.steps_per_block, model=args.model, model_type=args.model_type,
        max_length=args.max_length, scan_num_proc=args.scan_num_proc,
        node_rank=args.node_rank, node_count=args.node_count,
        partial_wait_timeout=args.partial_wait_timeout,
    )
    print(
        f"sample_plan n_multi={meta['N_multi']} n_text={meta['N_text']} "
        f"eligible_multi={meta['eligible_N_multi']} eligible_text={meta['eligible_N_text']} "
        f"max_steps={meta['max_steps']} blocks={meta['total_blocks']} dir={args.output_dir}", flush=True
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
