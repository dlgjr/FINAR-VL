from __future__ import annotations

import argparse
import py_compile
import re
import shutil
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_regex_once(text: str, pattern: str, new: str, label: str) -> str:
    updated, count = re.subn(pattern, new, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return updated


def read_lf(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


def write_lf(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def backup_once(path: Path) -> Path:
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    return backup


def patch_sample_plan(path: Path, multi_ratio: float) -> bool:
    text = read_lf(path)
    if "DEFAULT_MULTI_RATIO" in text and "--multi-ratio" in text:
        print(f"already patched: {path}")
        return False

    old_constants = '''ALPHA_SCHEDULE = ((0, 1000, 0.70), (1000, 3000, 0.50), (3000, float("inf"), 0.35))
HEAD_DOWNWEIGHT = {
    "chart_qa": 0.6,
    "table_math_qa": 0.6,
    "financial_multiple_choice": 0.5,
    "financial_headline_classification": 0.7,
    "financial_event_extraction": 0.7,
    "stock_movement_prediction": 0.7,
}
BENCHMARK_UPWEIGHT = {
    "basic_arithmetic_metrics": 1.5,
    "candlestick_ohlc_analysis": 1.5,
    "entity_extraction_classification": 1.5,
    "evidence_retrieval": 1.4,
    "long_document_cross_page_qa": 1.4,
    "document_finance_numeric_qa": 1.3,
    "table_math_reasoning": 1.3,
    "financial_chart_qa": 1.3,
    "compliance_safety_suitability": 1.5,
    "risk_sentiment_policy": 1.5,
    "investment_advice_strategy": 1.5,
    "portfolio_and_risk_management": 1.4,
    "financial_audit_and_controls": 1.5,
    "table_statistics_and_comparison": 1.4,
    "multi_table_reasoning": 1.4,
    "single_table_qa": 1.3,
    "financial_causal_event_reasoning": 1.4,
    "multimodal_financial_knowledge": 1.5,
    "financial_numerical_reasoning": 1.3,
    "financial_relation_extraction": 1.3,
    "long_document_cross_page": 1.4,
}
MAX_TASK_RATIO = 0.08
SMALL_TASK_MIN_N = 100
SMALL_TASK_MAX_N = 499
SMALL_TASK_RATIO = 0.02
TINY_TASK_MAX_N = 100  # 样本数不足 100 的 task 进 tiny pool
TINY_POOL_RATIO = 0.005
TINY_MAX_REPEAT = 2
UNKNOWN_TASK = "__unknown__"
_TINY_POOL_KEY = "__tiny_pool__"
'''
    new_constants = f'''DEFAULT_MULTI_RATIO = {multi_ratio:.6g}
ALPHA_SCHEDULE = ((0, 1000, 0.45), (1000, 3000, 0.40), (3000, float("inf"), 0.35))
HEAD_DOWNWEIGHT = {{
    "chart_qa": 0.30,
    "table_math_qa": 0.35,
    "financial_multiple_choice": 0.25,
    "financial_headline_classification": 0.40,
    "financial_event_extraction": 0.60,
    "stock_movement_prediction": 0.40,
    "general_dialogue": 0.35,
}}
BENCHMARK_UPWEIGHT = {{
    "basic_arithmetic_metrics": 1.3,
    "candlestick_trend_analysis": 1.5,
    "candlestick_ohlc_analysis": 1.6,
    "financial_chart_qa": 1.8,
    "document_ocr_qa": 1.3,
    "ocr_qa": 1.2,
    "entity_extraction_classification": 1.5,
    "evidence_retrieval": 2.5,
    "long_document_cross_page_qa": 2.5,
    "long_document_cross_page": 2.5,
    "financial_multipage_qa": 2.0,
    "document_finance_numeric_qa": 2.0,
    "table_math_reasoning": 2.2,
    "financial_numerical_reasoning": 2.2,
    "multi_table_reasoning": 2.5,
    "single_table_qa": 1.5,
    "table_statistics_and_comparison": 1.8,
    "compliance_safety_suitability": 1.6,
    "risk_sentiment_policy": 1.8,
    "investment_advice_strategy": 1.6,
    "portfolio_and_risk_management": 1.6,
    "financial_audit_and_controls": 1.6,
    "multimodal_financial_knowledge": 1.8,
    "financial_causal_event_reasoning": 1.8,
    "financial_causal_explanation": 1.8,
    "financial_relation_extraction": 2.2,
}}
MAX_TASK_RATIO = 0.08
SMALL_TASK_MIN_N = 100
SMALL_TASK_MAX_N = 499
SMALL_TASK_RATIO = 0.02
TINY_TASK_MAX_N = 100  # 样本数不足 100 的 task 进 tiny pool
TINY_POOL_RATIO = 0.005
TINY_MAX_REPEAT = 2
UNKNOWN_TASK = "__unknown__"
_TINY_POOL_KEY = "__tiny_pool__"
'''
    text = replace_regex_once(
        text,
        r'ALPHA_SCHEDULE = .*?_TINY_POOL_KEY = "__tiny_pool__"\n',
        new_constants,
        "constants",
    )

    old_tiny_weights = '''    tiny_tasks = sorted(task for task, count in counts.items() if count < TINY_TASK_MAX_N)
    weights: dict[str, float] = {}
    for task, count in counts.items():
        weights[task] = (count**alpha) * task_b_weight(task)
    if tiny_tasks:
        weights[_TINY_POOL_KEY] = sum(weights[task] for task in tiny_tasks)
'''
    new_tiny_weights = '''    tiny_tasks = sorted(task for task, count in counts.items() if count < TINY_TASK_MAX_N)
    weights: dict[str, float] = {
        task: (count**alpha) * task_b_weight(task)
        for task, count in counts.items()
        if task not in tiny_tasks
    }
    if tiny_tasks:
        weights[_TINY_POOL_KEY] = sum(
            (counts[task] ** alpha) * task_b_weight(task)
            for task in tiny_tasks
        )
'''
    text = replace_once(text, old_tiny_weights, new_tiny_weights, "tiny allocation")

    old_tiny_sampler = '''    picked: list[int] = []
    picked_set: set[int] = set()
    attempts = quota * 4 + 10
    for _ in range(attempts):
        if len(picked) >= quota:
            break
        candidates: list[int] = []
        candidate_weights: list[float] = []
        for task in tiny_tasks:
            weight = (len(task_index[task]) ** alpha) * task_b_weight(task)
            for index in task_index[task]:
                if usage.get((modality, index), 0) < TINY_MAX_REPEAT and index not in picked_set:
                    candidates.append(index)
                    candidate_weights.append(weight)
        if not candidates:
            break
        picked.append(rng.choices(candidates, weights=candidate_weights, k=1)[0])
        picked_set.add(picked[-1])
    for index in picked:
        usage[(modality, index)] = usage.get((modality, index), 0) + 1
    return picked
'''
    new_tiny_sampler = '''    picked: list[int] = []
    eligible = {
        task: [
            index
            for index in task_index[task]
            if usage.get((modality, index), 0) < TINY_MAX_REPEAT
        ]
        for task in tiny_tasks
    }
    eligible = {task: indices for task, indices in eligible.items() if indices}
    while len(picked) < quota and eligible:
        tasks = sorted(eligible)
        weights = [
            (len(task_index[task]) ** alpha) * task_b_weight(task)
            for task in tasks
        ]
        task = rng.choices(tasks, weights=weights, k=1)[0]
        index = rng.choice(eligible[task])
        eligible[task].remove(index)
        if not eligible[task]:
            del eligible[task]
        picked.append(index)
    for index in picked:
        usage[(modality, index)] = usage.get((modality, index), 0) + 1
    return picked
'''
    text = replace_once(text, old_tiny_sampler, new_tiny_sampler, "tiny sampler")

    old_build_signature = '''    grad_acc: int,
    seed: int,
    multi_index: dict[str, list[int]],
'''
    new_build_signature = '''    grad_acc: int,
    seed: int,
    multi_ratio: float,
    multi_index: dict[str, list[int]],
'''
    text = replace_once(text, old_build_signature, new_build_signature, "build_block signature")

    old_modality_quota = '''    samples_total = steps * global_batch_size
    multi_quota = samples_total // 2
    text_quota = samples_total - multi_quota
'''
    new_modality_quota = '''    samples_total = steps * global_batch_size
    multi_quota = int(samples_total * multi_ratio + 0.5)
    text_quota = samples_total - multi_quota
'''
    text = replace_once(text, old_modality_quota, new_modality_quota, "modality quota")

    old_micro_split = '''    micro_steps = steps * grad_acc
    per_micro = dp_world_size * per_device_batch
    # 每 step 该模态样本数 = global_batch_size // 2
    samples_per_step = global_batch_size // 2
    multi_sizes = _split_uneven(samples_per_step, grad_acc)
    entries: list[dict[str, Any]] = []
    multi_pos = text_pos = 0
    for micro_index in range(micro_steps):
        take_multi = multi_sizes[micro_index % grad_acc]
'''
    new_micro_split = '''    micro_steps = steps * grad_acc
    per_micro = dp_world_size * per_device_batch
    multi_per_step = _split_uneven(multi_quota, steps)
    rng.shuffle(multi_per_step)
    multi_sizes: list[int] = []
    for step_multi in multi_per_step:
        step_sizes = _split_uneven(step_multi, grad_acc)
        rng.shuffle(step_sizes)
        multi_sizes.extend(step_sizes)
    entries: list[dict[str, Any]] = []
    multi_pos = text_pos = 0
    for micro_index in range(micro_steps):
        take_multi = multi_sizes[micro_index]
'''
    text = replace_once(text, old_micro_split, new_micro_split, "micro-step split")

    old_generate_signature = '''    seed: int,
    max_steps: int | None = None,
    epochs: int = 1,
'''
    new_generate_signature = '''    seed: int,
    multi_ratio: float = DEFAULT_MULTI_RATIO,
    max_steps: int | None = None,
    epochs: int = 1,
'''
    text = replace_once(text, old_generate_signature, new_generate_signature, "generate_plan signature")

    old_validation = '''    if global_batch_size != dp_world_size * per_device_batch * grad_acc:
        raise ValueError(
'''
    new_validation = '''    if not 0.0 < multi_ratio < 1.0:
        raise ValueError(f"multi_ratio must be between 0 and 1, got {multi_ratio}")
    if global_batch_size != dp_world_size * per_device_batch * grad_acc:
        raise ValueError(
'''
    text = replace_once(text, old_validation, new_validation, "ratio validation")

    old_build_call = '''            grad_acc=grad_acc,
            seed=seed,
            multi_index=multi_index,
'''
    new_build_call = '''            grad_acc=grad_acc,
            seed=seed,
            multi_ratio=multi_ratio,
            multi_index=multi_index,
'''
    text = replace_once(text, old_build_call, new_build_call, "build_block call")

    old_meta = '''        "seed": seed,
        "epochs": epochs,
        "blocks": blocks,
'''
    new_meta = '''        "seed": seed,
        "epochs": epochs,
        "multi_ratio": multi_ratio,
        "text_ratio": 1.0 - multi_ratio,
        "blocks": blocks,
'''
    text = replace_once(text, old_meta, new_meta, "meta ratio")

    old_parser = '''    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-steps", type=int, default=None)
'''
    new_parser = '''    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--multi-ratio", type=float, default=DEFAULT_MULTI_RATIO)
    parser.add_argument("--max-steps", type=int, default=None)
'''
    text = replace_once(text, old_parser, new_parser, "CLI argument")

    old_main_call = '''        grad_acc=args.grad_acc,
        seed=args.seed,
        max_steps=args.max_steps,
'''
    new_main_call = '''        grad_acc=args.grad_acc,
        seed=args.seed,
        multi_ratio=args.multi_ratio,
        max_steps=args.max_steps,
'''
    text = replace_once(text, old_main_call, new_main_call, "main call")

    old_print = '''        f"max_steps={meta['max_steps']} blocks={meta['total_blocks']} "
        f"dir={args.output_dir}",
'''
    new_print = '''        f"max_steps={meta['max_steps']} blocks={meta['total_blocks']} "
        f"multi_ratio={meta['multi_ratio']:.3f} dir={args.output_dir}",
'''
    text = replace_once(text, old_print, new_print, "summary print")

    backup = backup_once(path)
    write_lf(path, text)
    py_compile.compile(str(path), doraise=True)
    print(f"patched: {path}")
    print(f"backup:  {backup}")
    return True


def patch_start_sft(path: Path, multi_ratio: float) -> bool:
    text = read_lf(path)
    if "SFT_MULTI_RATIO" in text and '--multi-ratio "$SFT_MULTI_RATIO"' in text:
        print(f"already patched: {path}")
        return False

    old_export = '''export SFT_PLAN_SEED="${SFT_PLAN_SEED:-42}"
export SFT_EPOCHS="${SFT_EPOCHS:-1}"
'''
    new_export = f'''export SFT_PLAN_SEED="${{SFT_PLAN_SEED:-42}}"
export SFT_MULTI_RATIO="${{SFT_MULTI_RATIO:-{multi_ratio:.6g}}}"
export SFT_EPOCHS="${{SFT_EPOCHS:-1}}"
'''
    text = replace_once(text, old_export, new_export, "start_sft ratio export")

    old_command = '''    --grad-acc 2 \\
    --seed "$SFT_PLAN_SEED" \\
    --epochs "$SFT_EPOCHS"
'''
    new_command = '''    --grad-acc 2 \\
    --seed "$SFT_PLAN_SEED" \\
    --multi-ratio "$SFT_MULTI_RATIO" \\
    --epochs "$SFT_EPOCHS"
'''
    text = replace_once(text, old_command, new_command, "start_sft plan argument")

    old_echo = '''  echo "max_steps=from_sample_plan max_length=49152 global_batch=28 per_device_batch=1 grad_accum=2"
'''
    new_echo = '''  echo "max_steps=from_sample_plan max_length=49152 global_batch=28 per_device_batch=1 grad_accum=2 multi_ratio=$SFT_MULTI_RATIO"
'''
    text = replace_once(text, old_echo, new_echo, "start_sft config output")

    backup = backup_once(path)
    write_lf(path, text)
    print(f"patched: {path}")
    print(f"backup:  {backup}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch FINAR-VL SFT sampler")
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--multi-ratio", type=float, default=0.45)
    args = parser.parse_args()

    if not 0.0 < args.multi_ratio < 1.0:
        raise SystemExit("--multi-ratio must be between 0 and 1")

    root = args.root.resolve() if args.root else Path(__file__).resolve().parent.parent
    sample_plan = root / "scripts" / "sft" / "sample_plan.py"
    start_sft = root / "scripts" / "dlc" / "start_sft.sh"
    for path in (sample_plan, start_sft):
        if not path.is_file():
            raise SystemExit(f"missing file: {path}")

    patch_sample_plan(sample_plan, args.multi_ratio)
    patch_start_sft(start_sft, args.multi_ratio)
    print(f"done: multi={args.multi_ratio:.2%}, text={1.0 - args.multi_ratio:.2%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
