import torch
from ..kernels import arith

class OpGlobalScale(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, scale : float):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        out = torch.empty(x.size(), device=x.device, dtype=torch.half)

        arith.arith_global_scale(
            x.numel(), x.data_ptr(),
            scale,
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        ctx.scale = scale
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.half
        grad = torch.empty(grad_output.size(), device=grad_output.device, dtype=torch.half)
        arith.arith_global_scale(
            grad_output.numel(), grad_output.data_ptr(),
            ctx.scale,
            grad.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad, None

def global_scale(x : torch.Tensor, scale : float) -> torch.Tensor:
    """
    out = x * scale
    """
    return OpGlobalScale.apply(x, scale)

def global_scaleTH(x : torch.Tensor, scale : float) -> torch.Tensor:
    """
    out = x * scale
    """
    return x * scale

def global_scale_inplace(x : torch.Tensor, scale : float) -> None:
    """
    x *= scale
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    arith.arith_global_scale(
        x.numel(), x.data_ptr(),
        scale,
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

class OpElementAdd(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, y : torch.Tensor):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        assert y.is_cuda and y.is_contiguous() and y.dtype == torch.half
        assert x.device == y.device and x.size() == y.size()
        out = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_element_add(
            x.size(0),
            x.stride(0),
            x.data_ptr(),
            y.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return out
    
    @staticmethod
    def backward(ctx, grad_output):
        return grad_output, grad_output


def element_add(x : torch.Tensor, y : torch.Tensor) -> torch.Tensor:
    """
    out = x + y
    """
    return OpElementAdd.apply(x, y)

def element_add_inplace(x : torch.Tensor, y : torch.Tensor) -> None:
    """
    x += y
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert y.is_cuda and y.is_contiguous() and y.dtype == torch.half
    assert x.device == y.device
    arith.arith_element_add(
        x.size(0),
        x.stride(0),
        x.data_ptr(),
        y.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

@torch.jit.script
def element_addTH(x : torch.Tensor, y : torch.Tensor) -> torch.Tensor:
    """
    out = x + y
    """
    return x + y

class OpElementMul(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, y : torch.Tensor):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        assert y.is_cuda and y.is_contiguous() and y.dtype == torch.half
        assert x.device == y.device and x.size() == y.size()
        out = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_element_mul(
            x.size(0),
            x.stride(0),
            x.data_ptr(),
            y.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        ctx.save_for_backward(x, y)
        return out
    
    @staticmethod
    def backward(ctx, grad_output):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.half
        x, y = ctx.saved_tensors
        grad_x = torch.empty(x.size(), device=x.device, dtype=torch.half)
        grad_y = torch.empty(y.size(), device=y.device, dtype=torch.half)
        arith.arith_element_mul(
            x.size(0),
            x.stride(0),
            grad_output.data_ptr(),
            y.data_ptr(),
            grad_x.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        arith.arith_element_mul(
            y.size(0),
            y.stride(0),
            x.data_ptr(),
            grad_output.data_ptr(),
            grad_y.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad_x, grad_y

def element_mul(x : torch.Tensor, y : torch.Tensor) -> torch.Tensor:
    """
    out = x * y
    """
    return OpElementMul.apply(x, y)

def element_mul_inplace(x : torch.Tensor, y : torch.Tensor) -> None:
    """
    x *= y
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert y.is_cuda and y.is_contiguous() and y.dtype == torch.half
    assert x.device == y.device and x.size() == y.size()
    arith.arith_element_mul(
        x.size(0),
        x.stride(0),
        x.data_ptr(),
        y.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

@torch.jit.script
def element_mulTH(x : torch.Tensor, y : torch.Tensor) -> torch.Tensor:
    """
    out = x * y
    """
    return x * y

class OpBatchedAdd(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, y : torch.Tensor):
        assert x.is_contiguous() and x.is_cuda and x.dtype == torch.float16
        assert y.is_contiguous() and y.is_cuda and y.dtype == torch.float16
        assert x.device == y.device
        assert x.size()[1:] == y.size()

        out = torch.empty(x.size(), device=x.device, dtype=x.dtype)
        arith.arith_batch_add_forward(
            x.size(0),
            x.stride(0),
            x.data_ptr(),
            y.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return out

    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_contiguous() and grad_output.is_cuda and grad_output.dtype == torch.float16
        grad_y = torch.empty( grad_output.size()[1:], device=grad_output.device, dtype=grad_output.dtype)
        arith.arith_batch_add_backward(
            grad_output.size(0),
            grad_output.stride(0),
            grad_output.data_ptr(),
            grad_y.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad_output, grad_y

def batched_add(x : torch.Tensor, y : torch.Tensor) -> torch.Tensor:
    """
    out = x + y[None, :]
    """
    return OpBatchedAdd.apply(x, y)

def batched_add_inplace(x : torch.Tensor, y : torch.Tensor) -> None:
    """
    x += y[None, :]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert y.is_cuda and y.is_contiguous() and y.dtype == torch.half
    assert x.device == y.device
    assert x.size()[1:] == y.size()

    arith.arith_batch_add_forward(
        x.size(0),
        x.stride(0),
        x.data_ptr(),
        y.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )
    
@torch.jit.script
def batched_addTH(x : torch.Tensor, y : torch.Tensor) -> torch.Tensor:
    """
    out = x + y[None, :]
    """
    return x + y[None, :]

class OpLnMulAdd(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
        assert beta.is_cuda and beta.is_contiguous() and beta.dtype == torch.half
        assert x.device == alpha.device and x.device == beta.device
        assert x.ndim == 3 and alpha.ndim == 1 and beta.ndim == 1
        batch, n, m = x.size()
        assert alpha.size(0) == n and beta.size(0) == n

        out = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_ln_mul_add(
            batch, n, m,
            x.data_ptr(),
            alpha.data_ptr(),
            beta.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        ctx.save_for_backward(x, alpha)
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.half
        assert grad_output.ndim == 3
        batch, n, m = grad_output.size()
        x, alpha = ctx.saved_tensors
        grad_alpha = torch.empty(alpha.size(), device=alpha.device, dtype=torch.half)
        grad_x = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_ln_mul(
            batch, n, m,
            grad_output.data_ptr(),
            alpha.data_ptr(),
            grad_x.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        arith.arith_ln_mul_backward(
            batch, n, m,
            x.data_ptr(),
            grad_output.data_ptr(),
            grad_alpha.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        grad_beta = torch.empty((n,), device=x.device, dtype=torch.half)
        arith.arith_ln_add_backward(
            batch, n, m,
            grad_output.data_ptr(),
            grad_beta.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad_x, grad_alpha, grad_beta

def ln_mul_add(x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor) -> torch.Tensor:
    """
    out = x * alpha[None, :, None] + beta[None, :, None]
    """
    return OpLnMulAdd.apply(x, alpha, beta)

def ln_mul_add_inplace(x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor) -> None:
    """
    x = x * alpha[None, :, None] + beta[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
    assert beta.is_cuda and beta.is_contiguous() and beta.dtype == torch.half
    assert x.device == alpha.device and x.device == beta.device
    assert x.ndim == 3 and alpha.ndim == 1 and beta.ndim == 1
    batch, n, m = x.size()
    assert alpha.size(0) == n and beta.size(0) == n

    arith.arith_ln_mul_add(
        batch, n, m,
        x.data_ptr(),
        alpha.data_ptr(),
        beta.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

@torch.jit.script
def ln_mul_addTH(x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor) -> torch.Tensor:
    """
    out = x * alpha[None, :, None] + beta[None, :, None]
    """
    return x * alpha[None, :, None] + beta[None, :, None]

class OpLnMul(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, alpha : torch.Tensor):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
        assert x.device == alpha.device
        assert x.ndim == 3 and alpha.ndim == 1
        batch, n, m = x.size()
        assert alpha.size(0) == n

        out = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_ln_mul(
            batch, n, m,
            x.data_ptr(),
            alpha.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        ctx.save_for_backward(x, alpha)
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.half
        assert grad_output.ndim == 3
        batch, n, m = grad_output.size()
        x, alpha = ctx.saved_tensors
        grad_alpha = torch.empty(alpha.size(), device=alpha.device, dtype=torch.half)
        grad_x = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_ln_mul(
            batch, n, m,
            grad_output.data_ptr(),
            alpha.data_ptr(),
            grad_x.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        arith.arith_ln_mul_backward(
            batch, n, m,
            x.data_ptr(),
            grad_output.data_ptr(),
            grad_alpha.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad_x, grad_alpha

def ln_mul(x : torch.Tensor, alpha : torch.Tensor) -> torch.Tensor:
    """
    out = x * alpha[None, :, None]
    """
    return OpLnMul.apply(x, alpha)

def ln_mul_inplace(x : torch.Tensor, alpha : torch.Tensor) -> None:
    """
    x = x * alpha[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
    assert x.device == alpha.device
    assert x.ndim == 3 and alpha.ndim == 1
    batch, n, m = x.size()
    assert alpha.size(0) == n

    arith.arith_ln_mul(
        batch, n, m,
        x.data_ptr(),
        alpha.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

@torch.jit.script
def ln_mulTH(x : torch.Tensor, alpha : torch.Tensor) -> torch.Tensor:
    """
    out = x * alpha[None, :, None]
    """
    return x * alpha[None, :, None]

class OpLnAdd(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x : torch.Tensor, beta : torch.Tensor):
        assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
        assert beta.is_cuda and beta.is_contiguous() and beta.dtype == torch.half
        assert x.device == beta.device
        assert x.ndim == 3 and beta.ndim == 1
        batch, n, m = x.size()
        assert beta.size(0) == n

        out = torch.empty(x.size(), device=x.device, dtype=torch.half)
        arith.arith_ln_add(
            batch, n, m,
            x.data_ptr(),
            beta.data_ptr(),
            out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.half
        assert grad_output.ndim == 3
        batch, n, m = grad_output.size()
        
        grad_beta = torch.empty((n,), device=grad_output.device, dtype=torch.half)
        arith.arith_ln_add_backward(
            batch, n, m,
            grad_output.data_ptr(),
            grad_beta.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
        return grad_output, grad_beta

def ln_add(x : torch.Tensor, beta : torch.Tensor) -> torch.Tensor:
    """
    out = x + beta[None, :, None]
    """
    return OpLnAdd.apply(x, beta)

def ln_add_inplace(x : torch.Tensor, beta : torch.Tensor) -> None:
    """
    x = x + beta[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert beta.is_cuda and beta.is_contiguous() and beta.dtype == torch.half
    assert x.device == beta.device
    assert x.ndim == 3 and beta.ndim == 1
    batch, n, m = x.size()
    assert beta.size(0) == n

    arith.arith_ln_add(
        batch, n, m,
        x.data_ptr(),
        beta.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

def ln_addTH(x : torch.Tensor, beta : torch.Tensor) -> torch.Tensor:
    """
    out = x + beta[None, :, None]
    """
    return x + beta[None, :, None]

def ln_sub_div(x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor) -> torch.Tensor:
    """
    out = (x - beta[None, :, None]) / alpha[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
    assert beta.is_cuda and beta.is_contiguous() and beta.dtype == torch.half
    assert x.device == alpha.device and x.device == beta.device
    assert x.ndim == 3 and alpha.ndim == 1 and beta.ndim == 1
    batch, n, m = x.size()
    assert alpha.size(0) == n and beta.size(0) == n

    out = torch.empty(x.size(), device=x.device, dtype=torch.half)
    arith.arith_ln_sub_div(
        batch, n, m,
        x.data_ptr(),
        alpha.data_ptr(),
        beta.data_ptr(),
        out.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )
    return out

def ln_sub_div_inplace(x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor) -> None:
    """
    x = (x - beta[None, :, None]) / alpha[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
    assert beta.is_cuda and beta.is_contiguous() and beta.dtype == torch.half
    assert x.device == alpha.device and x.device == beta.device
    assert x.ndim == 3 and alpha.ndim == 1 and beta.ndim == 1
    batch, n, m = x.size()
    assert alpha.size(0) == n and beta.size(0) == n

    arith.arith_ln_sub_div(
        batch, n, m,
        x.data_ptr(),
        alpha.data_ptr(),
        beta.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

@torch.jit.script
def ln_sub_divTH(x : torch.Tensor, alpha : torch.Tensor, beta : torch.Tensor) -> torch.Tensor:
    """
    out = (x - beta[None, :, None]) / alpha[None, :, None]
    """
    return (x - beta[None, :, None]) / alpha[None, :, None]


def ln_div(x : torch.Tensor, alpha : torch.Tensor) -> torch.Tensor:
    """
    out = x / alpha[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
    assert x.device == alpha.device
    assert x.ndim == 3 and alpha.ndim == 1
    batch, n, m = x.size()
    assert alpha.size(0) == n

    out = torch.empty(x.size(), device=x.device, dtype=torch.half)
    arith.arith_ln_div(
        batch, n, m,
        x.data_ptr(),
        alpha.data_ptr(),
        out.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )
    return out

def ln_div_inplace(x : torch.Tensor, alpha : torch.Tensor) -> None:
    """
    x = x / alpha[None, :, None]
    """
    assert x.is_cuda and x.is_contiguous() and x.dtype == torch.half
    assert alpha.is_cuda and alpha.is_contiguous() and alpha.dtype == torch.half
    assert x.device == alpha.device
    assert x.ndim == 3 and alpha.ndim == 1
    batch, n, m = x.size()
    assert alpha.size(0) == n

    arith.arith_ln_div(
        batch, n, m,
        x.data_ptr(),
        alpha.data_ptr(),
        x.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )

def ln_divTH(x : torch.Tensor, alpha : torch.Tensor) -> torch.Tensor:
    """
    out = x / alpha[None, :, None]
    """
    return x / alpha[None, :, None]

