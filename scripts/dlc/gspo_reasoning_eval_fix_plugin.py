"""Final guards for the fixed 50-row reasoning evaluation.

This module is imported last by ``gspo_plugins``. It intentionally does two
things only:
1. force the reasoning eval to the exact 50-row clean benchmark with no accidental
   20-sample cap;
2. extract only the terminal answer from a reasoning response, then use the same
   canonical numeric reward semantics as training for numeric questions while
   preserving the repository's existing deterministic rules for non-numeric tasks.
"""

from __future__ import annotations

import os
from pathlib import Path

import scripts.dlc.gspo_reasoning_policy_plugin as reasoning_policy
import scripts.sft.pass_at_8_eval as eval_module
from scripts.rl.gspo_reward import extract_final_answer, score_programmatic_answer


ROOT = Path(os.environ.get("QWEN3VL_ROOT", "/mnt/nas/duolg/qwen3vl"))
EVAL_DATA = ROOT / "data" / "benchmark" / "reasoning_calc_seen_50_clean.jsonl"
EXPECTED_ROWS = 50

if not EVAL_DATA.is_file():
    raise FileNotFoundError(EVAL_DATA)

row_count = sum(1 for line in EVAL_DATA.open(encoding="utf-8") if line.strip())
if row_count != EXPECTED_ROWS:
    raise RuntimeError(
        f"reasoning eval benchmark must contain exactly {EXPECTED_ROWS} non-empty rows, "
        f"got {row_count}: {EVAL_DATA}"
    )

# Force these values after all shared/default env files have been sourced. This
# prevents a stale GSPO_EVAL_MAX_SAMPLES=20 from silently evaluating only a
# hardest/image-heavy subset of the fixed 50-row file.
os.environ["GSPO_EVAL_DATA"] = str(EVAL_DATA)
os.environ["GSPO_EVAL_MAX_SAMPLES"] = str(EXPECTED_ROWS)


def _judge_reasoning_generation(row: dict, reference: str, candidate: str) -> dict:
    """Judge only the terminal answer, sharing numeric semantics with training."""
    verifier_type = eval_module._benchmark_verifier_type(row, reference)
    terminal = extract_final_answer(candidate, verifier_type)

    if terminal is None:
        correct = False
        extracted = eval_module.extract_answer(candidate)
        judge = "programmatic_terminal_missing"
    elif verifier_type in {"numeric", "numeric_final", "composite_numeric"}:
        reference_answer = eval_module.extract_answer(reference)
        question = str(row.get("messages", [{}])[0].get("content", ""))
        score = score_programmatic_answer(
            terminal,
            [reference_answer],
            verifier_type,
            question=question,
        )
        correct = score >= 1.0 - 1e-12
        extracted = terminal
        judge = "programmatic_reward_precision"
    else:
        # Preserve the repository's existing deterministic non-numeric rules.
        verdict = eval_module.programmatic_judge(
            reference,
            terminal,
            task=str(row.get("task", "")),
        )
        if verdict is None:
            verdict = eval_module._benchmark_programmatic_judge(row, reference, terminal)
            judge = "programmatic_reward_fallback"
        else:
            judge = "programmatic_terminal"
        correct = bool(verdict)
        extracted = terminal

    return {
        "text": candidate,
        "extracted_answer": extracted,
        "correct": bool(correct),
        "judge": judge,
    }


# _evaluate_reasoning_row resolves this module global at call time, so replacing
# it here updates Pass@1 and Pass@8 without duplicating the generation path.
reasoning_policy._judge_reasoning_generation = _judge_reasoning_generation

if reasoning_policy._rank() == 0:
    print(
        f"[GSPO_EVAL_CONFIG] dataset={EVAL_DATA} rows={row_count} "
        f"max_samples={EXPECTED_ROWS} verifier=terminal_shared_numeric_precision_window",
        flush=True,
    )
