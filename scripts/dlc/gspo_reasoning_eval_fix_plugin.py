"""Final guards for the fixed 50-row reasoning evaluation.

This module is imported last by ``gspo_plugins``. It intentionally does two
things only:
1. force the reasoning eval to the exact 50-row clean benchmark with no accidental
   20-sample cap;
2. judge numeric answers from the terminal answer's displayed numeric value while
   ignoring presentation-only units that are absent from the benchmark reference
   (for example reference ``26.74`` vs terminal ``26.74%``).

Training reward semantics are not changed.
"""

from __future__ import annotations

import os
from pathlib import Path

import scripts.dlc.gspo_reasoning_policy_plugin as reasoning_policy
import scripts.sft.pass_at_8_eval as eval_module
from scripts.rl.gspo_reward import _numeric_atoms, _parse_numeric, extract_final_answer, score_programmatic_answer


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


def _numeric_display_match(reference: str, candidate: str, verifier_type: str) -> tuple[bool, str | None]:
    """Compare terminal numeric display values, not units missing from benchmark gold.

    The clean benchmark stores answers such as ``26.74`` or ``15.1`` without a
    unit, while a correct reasoning response can naturally end in ``26.74%`` or
    ``15.1亿元``. The training reward's structured unit semantics remain untouched;
    this relaxation applies only to this benchmark evaluator.
    """

    terminal = extract_final_answer(candidate, verifier_type)
    if terminal is None:
        return False, None

    reference_answer = eval_module.extract_answer(reference)
    reference_atoms = _numeric_atoms(reference_answer)
    prediction_atoms = _numeric_atoms(terminal)
    if not reference_atoms or not prediction_atoms:
        return False, terminal

    try:
        reference_value = _parse_numeric(reference_atoms[-1]).value
        prediction_value = _parse_numeric(prediction_atoms[-1]).value
    except (TypeError, ValueError):
        return False, terminal

    # Reuse the GSPO numeric tolerance after stripping presentation-only units.
    correct = score_programmatic_answer(
        str(prediction_value),
        [str(reference_value)],
        "numeric",
    ) >= 1.0 - 1e-12
    return bool(correct), terminal


def _judge_reasoning_generation(row: dict, reference: str, candidate: str) -> dict:
    verifier_type = eval_module._benchmark_verifier_type(row, reference)

    if verifier_type == "numeric":
        correct, terminal = _numeric_display_match(reference, candidate, verifier_type)
        extracted = terminal if terminal is not None else eval_module.extract_answer(candidate)
        judge = "programmatic_terminal_numeric"
    else:
        correct = eval_module._benchmark_programmatic_judge(row, reference, candidate)
        extracted = extract_final_answer(candidate, verifier_type) or eval_module.extract_answer(candidate)
        judge = "programmatic_reward"

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
        f"max_samples={EXPECTED_ROWS} terminal_numeric_units=display_only",
        flush=True,
    )
