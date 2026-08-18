"""Compatibility entry point for the FINAR SFT plugin.

The implementation is kept in ``swift_sft_plugin_impl.py``. Runtime sample
replacement must be installed only after ``Seq2SeqTrainer.__init__`` has
assigned ``train_dataset``/``data_collator``. ms-swift constructs callbacks
before those attributes exist, so this shim defers only that installation until
the first ``get_train_dataloader()`` call.
"""

from __future__ import annotations

import types
from pathlib import Path

from scripts.sft import swift_sft_plugin_impl as _impl


# Preserve the historical import surface, including private helpers used by the
# SFT tests and the KL plugin. Function/class globals still point at _impl,
# which is intentional: patching the two installer globals below changes the
# behavior of the already-registered FinarPlanCallback without copying it.
globals().update({
    name: value
    for name, value in vars(_impl).items()
    if not name.startswith("__")
})

# External plugins can be loaded by file path under a non-package module name,
# while later code imports scripts.sft.swift_sft_plugin normally. Preserve the
# true implementation functions on _impl so a second execution of this shim
# never mistakes an already-patched function for the original.
if not hasattr(_impl, "_finar_original_install_runtime_replacement"):
    _impl._finar_original_install_runtime_replacement = _impl._install_runtime_replacement
if not hasattr(_impl, "_finar_original_install_plan_dataloader"):
    _impl._finar_original_install_plan_dataloader = _impl._install_plan_dataloader

_ORIGINAL_INSTALL_RUNTIME_REPLACEMENT = _impl._finar_original_install_runtime_replacement
_ORIGINAL_INSTALL_PLAN_DATALOADER = _impl._finar_original_install_plan_dataloader


def _defer_runtime_replacement(trainer, plan_dir: Path, tracker) -> None:
    """Record replacement state without touching trainer.train_dataset yet."""
    trainer._finar_runtime_replacement_pending = (Path(plan_dir), tracker)
    trainer._finar_runtime_replacement_installed = False


def _install_plan_dataloader_deferred(trainer) -> bool:
    """Install the plan dataloader and resolve replacement on first use."""
    installed = _ORIGINAL_INSTALL_PLAN_DATALOADER(trainer)
    if not installed:
        return False

    planned_get_train_dataloader = trainer.get_train_dataloader

    def deferred_get_train_dataloader(self, *args, **kwargs):
        if not bool(getattr(self, "_finar_runtime_replacement_installed", False)):
            pending = getattr(self, "_finar_runtime_replacement_pending", None)
            if pending is None:
                raise RuntimeError("runtime replacement state missing before train dataloader creation")
            plan_dir, tracker = pending
            # At this point Trainer.__init__ is complete: train_dataset,
            # template and data_collator are all available. Wrap them exactly
            # once, before PlanSampler/DataLoaderShard capture them.
            _ORIGINAL_INSTALL_RUNTIME_REPLACEMENT(self, Path(plan_dir), tracker)
            self._finar_runtime_replacement_installed = True
            self._finar_runtime_replacement_pending = None
        return planned_get_train_dataloader(*args, **kwargs)

    trainer.get_train_dataloader = types.MethodType(deferred_get_train_dataloader, trainer)
    return True


# FinarPlanCallback was defined in _impl, so its global lookups resolve through
# the _impl module. Replace only these two helpers; all sampling/accounting
# behavior remains the existing implementation.
_impl._install_runtime_replacement = _defer_runtime_replacement
_impl._install_plan_dataloader = _install_plan_dataloader_deferred

# Keep direct imports from this compatibility module consistent with the
# patched behavior too.
_install_runtime_replacement = _defer_runtime_replacement
_install_plan_dataloader = _install_plan_dataloader_deferred
