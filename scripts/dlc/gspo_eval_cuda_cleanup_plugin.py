"""Post-evaluation CUDA cleanup for colocated GSPO/vLLM training.

Runs after the complete distributed evaluation returns and before training resumes.
The cleanup is intentionally narrow: collect dead Python objects, release PyTorch's
unused CUDA cache, synchronize all ranks, then synchronize CUDA once more.
"""

from __future__ import annotations

import scripts.dlc.gspo_trainer_plugin as trainer_plugin


if not getattr(trainer_plugin.run_distributed_evaluation, "_gspo_post_eval_cuda_cleanup", False):
    _original_run_distributed_evaluation = trainer_plugin.run_distributed_evaluation

    def _run_with_post_eval_cuda_cleanup(*args, **kwargs):
        metrics = _original_run_distributed_evaluation(*args, **kwargs)

        import gc
        import torch

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()

        if torch.distributed.is_available() and torch.distributed.is_initialized():
            torch.distributed.barrier()

        if torch.cuda.is_available():
            torch.cuda.synchronize()

        return metrics

    _run_with_post_eval_cuda_cleanup._gspo_post_eval_cuda_cleanup = True
    trainer_plugin.run_distributed_evaluation = _run_with_post_eval_cuda_cleanup
