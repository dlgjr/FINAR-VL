from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

gelu_kernel = Kernel(
    "gelu",
    [
        "cu_gelu_forward",
        "cu_gelu_backward",
    ]
)


def gelu_forward(
        batch : int,
        n : int,
        mat :  DevicePointer,
        out : DevicePointer,
        stream : CUDAStream
    ):
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    gelu_kernel.cu_gelu_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(out)
        ]
    )

def gelu_inplace_forward(
        batch : int,
        n : int,
        mat :  DevicePointer,
        stream : CUDAStream
    ):
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    gelu_kernel.cu_gelu_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(mat)
        ]
    )

def gelu_backward(
        batch : int,
        n : int,
        grad_out : DevicePointer,
        mat : DevicePointer,
        grad : DevicePointer,
        stream : CUDAStream
    ):
    threads = min(round_up(n, 32), 1024)
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    gelu_kernel.cu_gelu_backward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(grad)
        ]
    )
