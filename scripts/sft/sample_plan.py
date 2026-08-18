"""SFT sample-plan entrypoint with project-specific task overrides.

The implementation lives in sample_plan_base.py. Keeping the override here makes the
new accounting/audit task explicit without changing the rest of the sampler behavior.
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

# New benchmark-shaped accounting/audit reasoning data gets only a mild 1.2x
# task weight. All existing task weights remain unchanged.
_impl.MULTI_UPWEIGHT["accounting_audit_reasoning"] = 1.20
_impl.TEXT_UPWEIGHT["accounting_audit_reasoning"] = 1.20
_impl.TASK_TO_FAMILY["accounting_audit_reasoning"] = "accounting_valuation"

if __name__ == "__main__":
    raise SystemExit(_impl.main())

# Imported callers should see the original module object itself, so monkeypatching and
# function-global lookups behave exactly as before.
sys.modules[__name__] = _impl
