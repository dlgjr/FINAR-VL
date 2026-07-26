from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

softmax_kernel = Kernel(
    "softmax",
    [
        "cu_softmax_forward",
        "cu_softmax_inplace_forward",
        "cu_softmax_backward",
        "cu_softmax_step_inplace"
    ]
)

def softmax_forward(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m)
        out : DevicePointer,    # (batch, n, m)
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    softmax_kernel.cu_softmax_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(out)
        ]
    )

def softmax_inplace_forward(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m)
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    softmax_kernel.cu_softmax_inplace_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(inp)
        ]
    )

def softmax_backward(
        batch : int, n : int, m : int,
        out : DevicePointer,        # (batch, n, m)
        grad_out : DevicePointer,   # (batch, n, m)
        grad : DevicePointer,       # (batch, n, m)
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(m, 32) // 32, 1)
    blockDim = (32, 32, 1)
    softmax_kernel.cu_softmax_backward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(out),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(grad)
        ]
    )

def softmax_step_inplace(
        batch : int, n : int,
        x : DevicePointer,
        stream : CUDAStream
    ):
    gridDim = (batch, 1, 1)
    blockDim = (min(1024, round_up(n, 32)), 1, 1)
    softmax_kernel.cu_softmax_step_inplace(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(x)
        ]
    )