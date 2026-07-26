from typing import Optional
import torch
from ..kernels import has_nan_inf as kn_has_nan_inf

def has_nan_inf(x : torch.Tensor, out : Optional[torch.Tensor] = None) -> torch.Tensor:
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    if out is None:
        out = torch.empty(1, dtype=torch.bool, device=x.device)[0]
    kn_has_nan_inf(
        x.numel(), x.data_ptr(),
        out.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )
    return out