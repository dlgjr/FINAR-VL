import torch
from ..kernels import mask as mask_cuda

class OpMask(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, mask : torch.Tensor, value : float) -> torch.Tensor:
        assert x.is_contiguous() and x.is_cuda and x.dtype == torch.float16 and x.ndim == 3
        assert mask.is_contiguous() and mask.is_cuda and mask.dtype == torch.bool and mask.ndim == 2
        assert x.device == mask.device
        batch, n, m = x.size()
        assert mask.size() == (batch, m)

        out = torch.empty(x.size(), dtype=torch.float16, device=x.device)
        mask_cuda(
            batch, n, m,
            x.data_ptr(),
            mask.data_ptr(),
            value,
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        ctx.save_for_backward(mask)
        return out

    @staticmethod
    def backward(ctx, grad_output : torch.Tensor) -> torch.Tensor:
        mask = ctx.saved_tensors[0]
        batch, n, m = grad_output.size()
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.float16
        
        grad = torch.empty(grad_output.size(), dtype=torch.float16, device=grad_output.device)
        mask_cuda(
            batch, n, m,
            grad_output.data_ptr(),
            mask.data_ptr(),
            0.0,
            grad.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad, None, None


def mask(x : torch.Tensor, mask : torch.Tensor, value : float) -> torch.Tensor:
    return OpMask.apply(x, mask, value)

def mask_inplace(x : torch.Tensor, mask : torch.Tensor, value : float) -> None:
    assert x.is_contiguous() and x.is_cuda and x.dtype == torch.float16 and x.ndim == 3
    assert mask.is_contiguous() and mask.is_cuda and mask.dtype == torch.bool and mask.ndim == 2
    assert x.device == mask.device
    batch, n, m = x.size()
    assert mask.size() == (batch, m)

    mask_cuda(
        batch, n, m,
        x.data_ptr(),
        mask.data_ptr(),
        value,
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

def maskTH(x : torch.Tensor, mask : torch.Tensor, value : float) -> torch.Tensor:
    return torch.where(
        mask[:, None, :],
        x,
        torch.scalar_tensor(value, device=x.device, dtype=x.dtype),
    )
