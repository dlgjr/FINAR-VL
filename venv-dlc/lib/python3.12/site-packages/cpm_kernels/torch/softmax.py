import torch
from ..kernels import softmax_forward, softmax_backward, softmax_inplace_forward

class OpSoftmax(torch.autograd.Function):
    """
    Softmax dim=1
    """
    @staticmethod
    def forward(ctx, x : torch.Tensor):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        assert x.ndim == 3
        out = torch.empty(x.size(), device=x.device, dtype=torch.half)
        softmax_forward(
            x.size(0), x.size(1), x.size(2),
            x.data_ptr(), out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        ctx.save_for_backward(out)
        return out
        
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.half
        assert grad_output.ndim == 3
        out = ctx.saved_tensors[0]
        grad = torch.empty(grad_output.size(), device=grad_output.device, dtype=torch.half)
        softmax_backward(
            grad_output.size(0), grad_output.size(1), grad_output.size(2),
            out.data_ptr(), 
            grad_output.data_ptr(),
            grad.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad

def softmax(x : torch.Tensor) -> torch.Tensor:
    return OpSoftmax.apply(x)

def softmaxTH(x : torch.Tensor) -> torch.Tensor:
    return torch.nn.functional.softmax(x, dim=1)

def softmax_inplace(x : torch.Tensor) -> None:
    assert x.is_cuda and x.ndim == 3 and x.is_contiguous() and x.dtype == torch.half
    softmax_inplace_forward(
        x.size(0), x.size(1), x.size(2),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )