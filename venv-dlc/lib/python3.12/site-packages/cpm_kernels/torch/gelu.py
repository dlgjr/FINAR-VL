import torch
from ..kernels import gelu_forward, gelu_backward, gelu_inplace_forward

class OpGeLU(torch.autograd.Function):
    """
    Element wised GeLU function.
    Input:
        - x (batch, *)
    Output:
        - y (batch, *)
    """

    @staticmethod
    def forward(ctx, x : torch.Tensor):
        assert x.is_contiguous() and x.is_cuda and x.dtype == torch.half
        ctx.save_for_backward(x)
        ret = torch.empty_like(x)
        gelu_forward(
            x.size(0),
            x.stride(0),
            x.data_ptr(),
            ret.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return ret
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        x = ctx.saved_tensors[0]
        grad = torch.empty_like(grad_output)

        assert grad_output.is_contiguous() and grad_output.is_cuda and grad_output.dtype == torch.half
        gelu_backward(
            x.size(0),
            x.stride(0),
            grad_output.data_ptr(),
            x.data_ptr(),
            grad.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad

def gelu(x : torch.Tensor) -> torch.Tensor:
    return OpGeLU.apply(x)


@torch.jit.script
def gelu_impl(x):
    """OpenAI's gelu implementation."""
    return 0.5 * x * (1.0 + torch.tanh(0.7978845608028654 * x *
                                       (1.0 + 0.044715 * x * x)))

def geluTH(x : torch.Tensor):
    return gelu_impl(x)

def gelu_inplace(x : torch.Tensor) -> None:
    assert x.is_contiguous() and x.is_cuda and x.dtype == torch.half
    gelu_inplace_forward(
        x.size(0),
        x.stride(0),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )