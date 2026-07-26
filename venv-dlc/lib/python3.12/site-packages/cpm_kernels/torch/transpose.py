import torch
from ..kernels import transpose as trans_func


class OpTranspose(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor):
        assert x.is_contiguous() and x.is_cuda and x.dtype == torch.half and x.ndim == 3
        out = torch.empty((x.size(0), x.size(2), x.size(1)), dtype=torch.half, device=x.device)
        trans_func(
            x.size(0), x.size(1), x.size(2),
            x.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_contiguous() and grad_output.is_cuda and grad_output.dtype == torch.half and grad_output.ndim == 3
        grad = torch.empty((grad_output.size(0), grad_output.size(2), grad_output.size(1)), dtype=torch.half, device=grad_output.device)
        trans_func(
            grad_output.size(0), grad_output.size(1), grad_output.size(2),
            grad_output.data_ptr(),
            grad.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad 

def transpose(x : torch.Tensor) -> torch.Tensor:
    return OpTranspose.apply(x)

def transposeTH(x : torch.Tensor) -> torch.Tensor:
    assert x.ndim == 3
    return x.transpose(1, 2)