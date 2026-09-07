"""Relax GSPO numeric reward only when the gold answer omits its unit.

If structured gold carries an explicit unit/dimension, keep the original strict
verifier unchanged. If the gold is a unitless scalar (for example ``26.74``)
and the model writes the same displayed value with a presentation unit (for
example ``26.74%`` or ``15.1亿元``), treat the numeric value as matching.

This changes training reward semantics only for unit-omitted numeric gold; it
does not scan the reasoning body and still relies on the terminal-answer parser.
"""

from __future__ import annotations

import scripts.rl.gspo_reward as reward_module


if not getattr(reward_module._numeric_match, "_gspo_allow_omitted_gold_unit", False):
    _original_numeric_match = reward_module._numeric_match

    def _numeric_match_allow_omitted_gold_unit(pred, gold, spec=None):
        # A unitless gold cannot legitimately enforce a unit. Compare the
        # displayed numeric value first, regardless of the candidate's unit.
        # Example: gold=26.74, prediction=26.74% -> match.
        if gold.unit == "" and gold.dimension == "scalar":
            abs_tol, rel_tol = reward_module._numeric_tolerance(gold, spec)
            delta = abs(pred.value - gold.value)
            if delta <= abs_tol or delta <= abs(gold.value) * rel_tol:
                return True

        # Explicit-unit gold keeps the original strict dimension/unit logic.
        return _original_numeric_match(pred, gold, spec)

    _numeric_match_allow_omitted_gold_unit._gspo_allow_omitted_gold_unit = True
    reward_module._numeric_match = _numeric_match_allow_omitted_gold_unit

    print(
        "[GSPO_REWARD_CONFIG] unitless_numeric_gold=display_value_match "
        "explicit_unit_gold=strict terminal_answer_only=true",
        flush=True,
    )
