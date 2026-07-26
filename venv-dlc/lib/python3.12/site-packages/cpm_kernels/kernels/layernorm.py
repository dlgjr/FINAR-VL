from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

layernorm_kernel = Kernel(
    "layernorm",
    [
        "cu_layernorm_forward",
        "cu_layernorm_inplace_forward",
        "cu_layernorm_forward_v",
        "cu_layernorm_forward_mv",
        "cu_layernorm_backward_v",
        "cu_layernorm_backward_mv",
        "cu_layernorm_step",
        "cu_layernorm_step_inplace"
    ]
)

def layernorm_forward(
        batch : int, n : int, m : int,
        mat : DevicePointer,    # (batch, n, m)
        out : DevicePointer,    # (batch, n, m)
        eps : float,
        rd_mean : bool,
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    layernorm_kernel.cu_layernorm_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(out),
            ctypes.c_float(eps),
            ctypes.c_bool(rd_mean)
        ]
    )

def layernorm_inplace_forward(
        batch : int, n : int, m : int,
        mat : DevicePointer,    # (batch, n, m)
        eps : float,
        rd_mean : bool,
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    layernorm_kernel.cu_layernorm_inplace_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(mat),
            ctypes.c_float(eps),
            ctypes.c_bool(rd_mean)
        ]
    )

def layernorm_forward_v(
        batch : int, n : int, m : int,
        mat : DevicePointer,        # (batch, n, m)
        out : DevicePointer,        # (batch, n, m)
        out_var : DevicePointer,    # (batch, m)
        eps: float,
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    layernorm_kernel.cu_layernorm_forward_v(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(out),
            ctypes.c_void_p(out_var),
            ctypes.c_float(eps)
        ]
    )

def layernorm_forward_mv(
        batch : int, n : int, m : int,
        mat : DevicePointer,        # (batch, n, m)
        out : DevicePointer,        # (batch, n, m)
        out_mean : DevicePointer,   # (batch, m)
        out_var : DevicePointer,    # (batch, m)
        eps : float,
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    layernorm_kernel.cu_layernorm_forward_mv(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(out),
            ctypes.c_void_p(out_mean),
            ctypes.c_void_p(out_var),
            ctypes.c_float(eps)
        ]
    )

def layernorm_backward_v(
        batch : int, n : int, m : int,
        mat : DevicePointer,        # (batch, n, m)
        grad_out : DevicePointer,    # (batch, n, m)
        var : DevicePointer,        # (batch, m)
        grad : DevicePointer,    # (batch, n, m)
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    layernorm_kernel.cu_layernorm_backward_v(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(var),
            ctypes.c_void_p(grad)
        ]
    )

def layernorm_backward_mv(
        batch : int, n : int, m : int,
        mat : DevicePointer,        # (batch, n, m)
        grad_out : DevicePointer,   # (batch, n, m)
        mean : DevicePointer,       # (batch, m)
        var : DevicePointer,        # (batch, m)
        grad : DevicePointer,       # (batch, n, m)
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    layernorm_kernel.cu_layernorm_backward_mv(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(mean),
            ctypes.c_void_p(var),
            ctypes.c_void_p(grad)
        ]
    )

def layernorm_step(
        batch : int, n : int,
        mat : DevicePointer,        # (batch, n)    fp16
        out : DevicePointer,        # (batch, n)    fp16
        eps : float,
        rd_mean : bool,
        stream : CUDAStream
    ):
    gridDim = (batch, 1, 1)
    blockDim = (min(1024, round_up(n, 32)), 1, 1)
    layernorm_kernel.cu_layernorm_step(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(out),
            ctypes.c_float(eps),
            ctypes.c_bool(rd_mean)
        ]
    )

def layernorm_step_inplace(
        batch : int, n : int,
        mat : DevicePointer,        # (batch, n)    fp16
        eps : float,
        rd_mean : bool,
        stream : CUDAStream
    ):
    gridDim = (batch, 1, 1)
    blockDim = (min(1024, round_up(n, 32)), 1, 1)
    layernorm_kernel.cu_layernorm_step_inplace(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(mat),
            ctypes.c_float(eps),
            ctypes.c_bool(rd_mean)
        ]
    )