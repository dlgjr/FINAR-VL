"""SFT sample-plan entrypoint with project-specific task overrides.

The implementation lives in sample_plan_base.py. Keeping the override here makes the
benchmark-sensitive task policy explicit without changing the rest of the sampler behavior.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


_IMPL_PATH = Path(__file__).with_name("sample_plan_base.py")
_SPEC = importlib.util.spec_from_file_location("_finar_sample_plan_base", _IMPL_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load sample-plan implementation: {_IMPL_PATH}")
_impl = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _impl
_SPEC.loader.exec_module(_impl)

# Keep long-form supervision competitive instead of penalizing it by sqrt(length).
_impl.TOKEN_LENGTH_BETA = 0.25

# Mild task weights remain useful inside the guaranteed quota.
_impl.MULTI_UPWEIGHT["accounting_audit_reasoning"] = 1.20
_impl.TEXT_UPWEIGHT["accounting_audit_reasoning"] = 1.20
_impl.MULTI_DOWNWEIGHT["image_caption"] = 1.00
_impl.TASK_TO_FAMILY["accounting_audit_reasoning"] = "accounting_valuation"
_impl.TASK_TO_FAMILY["financial_visual_description"] = "document_perception"
_impl.TASK_TO_FAMILY["financial_ocr_transcription"] = "document_perception"

# Explicit minimum sample quotas within each modality. The visual/OCR proxies are
# protected together with the exact benchmark-side tasks, while the 1% insufficient-
# information floor is intentionally smaller because it exists in both modalities.
TASK_MIN_RATIO = {
    "financial_ocr": 0.04,
    "financial_ocr_transcription": 0.02,
    "financial_summarization": 0.02,
    "financial_visual_description": 0.02,
    "image_caption": 0.02,
    "insufficient_information_detection": 0.01,
    "accounting_audit_reasoning": 0.02,
}

# Leave enough family headroom for protected minima to survive token-based cap repair.
_impl.FAMILY_CAP["document_perception"] = max(_impl.FAMILY_CAP["document_perception"], 0.16)
_impl.FAMILY_CAP["generation_dialogue"] = max(_impl.FAMILY_CAP["generation_dialogue"], 0.15)
_impl.FAMILY_CAP["retrieval_grounding"] = max(_impl.FAMILY_CAP["retrieval_grounding"], 0.12)
_impl.FAMILY_CAP["accounting_valuation"] = max(_impl.FAMILY_CAP["accounting_valuation"], 0.16)

_ORIGINAL_ALLOCATE_QUOTAS = _impl.allocate_quotas
_ORIGINAL_BUILD_BLOCK = _impl.build_block


def allocate_quotas(counts, quota, alpha, modality, means=None):
    allocations, tiny_quota, tiny_tasks = _ORIGINAL_ALLOCATE_QUOTAS(counts, quota, alpha, modality, means)
    minimums = {
        task: min(_impl.task_cap(task, counts[task], quota), max(1, int(quota * ratio + 0.5)))
        for task, ratio in TASK_MIN_RATIO.items()
        if task in allocations
    }
    for task in sorted(minimums):
        need = minimums[task] - allocations.get(task, 0)
        while need > 0:
            donors = [
                donor for donor in allocations
                if donor != task and allocations[donor] > minimums.get(donor, 0)
            ]
            if not donors:
                break
            donor = max(donors, key=lambda name: (allocations[name] - minimums.get(name, 0), name))
            take = min(need, allocations[donor] - minimums.get(donor, 0))
            allocations[donor] -= take
            allocations[task] = allocations.get(task, 0) + take
            need -= take
    return allocations, tiny_quota, tiny_tasks


def build_block(**kwargs):
    entries, block_info, tiny_usage = _ORIGINAL_BUILD_BLOCK(**kwargs)
    parts = [
        f"block={block_info['block_id']}",
        f"steps={block_info['start_step']}-{block_info['start_step'] + block_info['steps']}",
    ]
    for modality in ("multi", "text"):
        quotas = block_info["quotas"][modality]
        for task in TASK_MIN_RATIO:
            if task in quotas:
                parts.append(f"{modality}:{task}={quotas[task]}")
        family = block_info["planned"][modality]["families"].get("document_perception")
        if family is not None:
            parts.append(f"{modality}:document_perception={family['samples']}({family['sample_ratio']:.3f})")
        retrieval = block_info["planned"][modality]["families"].get("retrieval_grounding")
        if retrieval is not None:
            parts.append(f"{modality}:retrieval_grounding={retrieval['samples']}({retrieval['sample_ratio']:.3f})")
    print("SFT_QUOTA | " + " ".join(parts), flush=True)
    return entries, block_info, tiny_usage


_impl.allocate_quotas = allocate_quotas
_impl.build_block = build_block
_impl.TASK_MIN_RATIO = TASK_MIN_RATIO

if __name__ == "__main__":
    raise SystemExit(_impl.main())

# Imported callers should see the original module object itself, so monkeypatching and
# function-global lookups behave exactly as before.
sys.modules[__name__] = _impl
