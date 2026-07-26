from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

arith_kernel = Kernel(
    "arith",
    [
        "cu_arith_global_scale",
        "cu_arith_element_add",
        "cu_arith_element_mul",
        "cu_arith_batch_add_forward",
        "cu_arith_batch_add_backward",
        "cu_arith_ln_mul_add",
        "cu_arith_ln_add",
        "cu_arith_ln_mul",
        "cu_arith_ln_div",
        "cu_arith_ln_sub_div",
        "cu_arith_ln_mul_backward",
        "cu_arith_ln_add_backward",
        "cu_arith_batch_mul_add",
        "cu_arith_batch_mul"
    ]
)

def arith_global_scale(
        n : int,
        inp : DevicePointer,    # (n,) fp16
        scale : float,
        out : DevicePointer,    # (n,) fp16
        stream : CUDAStream
    ):
    threads = min(round_up(n, 32), 1024)
    gridDim = (round_up(n, threads) // threads, 1, 1)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_global_scale(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(n),
            ctypes.c_void_p(inp),
            ctypes.c_float(scale),
            ctypes.c_void_p(out)
        ]
    )

def arith_element_add(
        batch : int, n : int,
        x : DevicePointer,    # (batch, n)  fp16
        y : DevicePointer,    # (batch, n)  fp16
        out : DevicePointer,  # (batch, n)  fp16
        stream : CUDAStream
    ):
    """
    out = x + y
    """
    assert n % 2 == 0
    n = n // 2
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_element_add(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_void_p(x),
            ctypes.c_void_p(y),
            ctypes.c_void_p(out)
        ]
    )

def arith_element_mul(
        batch : int, n : int,
        x : DevicePointer,    # (batch, n)  fp16
        y : DevicePointer,    # (batch, n)  fp16
        out : DevicePointer,  # (batch, n)  fp16
        stream : CUDAStream
    ):
    """
    out = x * y
    """
    assert n % 2 == 0
    n = n // 2
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_element_mul(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_void_p(x),
            ctypes.c_void_p(y),
            ctypes.c_void_p(out)
        ]
    )

def arith_batch_add_forward(
        batch : int, n : int,
        x : DevicePointer,    # (batch, n)  fp16
        y : DevicePointer,    # (n)  fp16
        out : DevicePointer,  # (batch, n)  fp16
        stream : CUDAStream
    ):
    """
    out = x + y[None, :]
    """
    assert n % 2 == 0
    n = n // 2
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_batch_add_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_void_p(x),
            ctypes.c_void_p(y),
            ctypes.c_void_p(out)
        ]
    )

def arith_batch_add_backward(
        batch : int, n : int,
        grad_out : DevicePointer,  # (batch, n) fp16
        grad : DevicePointer,      # (n) fp16
        stream : CUDAStream
    ):
    gridDim = ( round_up(n, 32) // 32, 1, 1 )
    blockDim = (32, 32, 1)
    arith_kernel.cu_arith_batch_add_backward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(grad)
        ]
    )

def arith_ln_mul_add(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m) fp16
        alpha : DevicePointer,  # (n)           fp16
        beta : DevicePointer,   # (n)           fp16
        out : DevicePointer,    # (batch, n, m) fp16
        stream : CUDAStream
    ):
    """
    out = x * alpha[None, :, None] + beta[None, :, None]
    """
    assert m % 2 == 0
    m = m // 2
    threads = min(round_up(m, 32), 1024)
    gridDim = (batch, n, round_up(m, threads) // threads)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_ln_mul_add(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(alpha),
            ctypes.c_void_p(beta),
            ctypes.c_void_p(out)
        ]
    )

def arith_ln_add(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m) fp16
        beta : DevicePointer,   # (n)           fp16
        out : DevicePointer,    # (batch, n, m) fp16
        stream : CUDAStream
    ):
    """
    out = x + beta[None, :, None]
    """
    assert m % 2 == 0
    m = m // 2
    threads = min(round_up(m, 32), 1024)
    gridDim = (batch, n, round_up(m, threads) // threads)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_ln_add(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(beta),
            ctypes.c_void_p(out)
        ]
    )


def arith_ln_mul(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m) fp16
        alpha : DevicePointer,  # (n)           fp16
        out : DevicePointer,    # (batch, n, m) fp16
        stream : CUDAStream
    ):
    """
    out = x * alpha[None, :, None]
    """
    assert m % 2 == 0
    m = m // 2
    threads = min(round_up(m, 32), 1024)
    gridDim = (batch, n, round_up(m, threads) // threads)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_ln_mul(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(alpha),
            ctypes.c_void_p(out)
        ]
    )

def arith_ln_div(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m) fp16
        alpha : DevicePointer,  # (n)           fp16
        out : DevicePointer,    # (batch, n, m) fp16
        stream : CUDAStream
    ):
    """
    out = x / alpha[None, :, None]
    """
    assert m % 2 == 0
    m = m // 2
    threads = min(round_up(m, 32), 1024)
    gridDim = (batch, n, round_up(m, threads) // threads)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_ln_div(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(alpha),
            ctypes.c_void_p(out)
        ]
    )

def arith_ln_sub_div(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m) fp16
        alpha : DevicePointer,  # (n)           fp16
        beta : DevicePointer,   # (n)           fp16
        out : DevicePointer,    # (batch, n, m) fp16
        stream : CUDAStream
    ):
    """
    out = (x - beta[None, :, None]) / alpha[None, :, None]
    """
    assert m % 2 == 0
    m = m // 2
    threads = min(round_up(m, 32), 1024)
    gridDim = (batch, n, round_up(m, threads) // threads)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_ln_sub_div(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(alpha),
            ctypes.c_void_p(beta),
            ctypes.c_void_p(out)
        ]
    )


def arith_ln_mul_backward(
    batch : int, n : int, m : int,
    inp : DevicePointer,        # (batch, n, m) fp16
    grad_out : DevicePointer,   # (batch, n, m) fp16
    grad : DevicePointer,       # (n) fp16
    stream : CUDAStream
):
    gridDim = (n, 1, 1)
    blockDim = (32, 32, 1)
    arith_kernel.cu_arith_ln_mul_backward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(grad)
        ]
    )

def arith_ln_add_backward(
    batch : int, n : int, m : int,
    grad_out : DevicePointer,   # (batch, n, m) fp16
    grad : DevicePointer,       # (n) fp16
    stream : CUDAStream
):
    gridDim = (n, 1, 1)
    blockDim = (32, 32, 1)
    arith_kernel.cu_arith_ln_add_backward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_int64(m),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(grad)
        ]
    )

def arith_batch_mul_add(
    batch : int, n : int,
    x : DevicePointer,      # (batch, n)
    alpha : DevicePointer,  # (n)
    beta : DevicePointer,   # (n)
    out : DevicePointer,    # (batch, n)
    stream : CUDAStream
):
    assert n % 2 == 0
    n = n // 2
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_batch_mul_add(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_void_p(x),
            ctypes.c_void_p(alpha),
            ctypes.c_void_p(beta),
            ctypes.c_void_p(out)
        ]
    )

def arith_batch_mul(
    batch : int, n : int,
    x : DevicePointer,      # (batch, n)
    alpha : DevicePointer,  # (n)
    out : DevicePointer,    # (batch, n)
    stream : CUDAStream
):
    assert n % 2 == 0
    n = n // 2
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    arith_kernel.cu_arith_batch_mul(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int64(batch),
            ctypes.c_int64(n),
            ctypes.c_void_p(x),
            ctypes.c_void_p(alpha),
            ctypes.c_void_p(out)
        ]
    )

