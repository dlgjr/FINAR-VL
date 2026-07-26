from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

transpose_kernel = Kernel(
    "transpose",
    [
        "cu_transpose"
    ]
)

def transpose(
        batch : int, n : int, m : int,
        inp : DevicePointer,
        out : DevicePointer,
        stream : CUDAStream
    ):
    gridDim = (batch, round_up(n, 32) // 32, round_up(m, 32) // 32)
    blockDim = (32, 32, 1)
    transpose_kernel.cu_transpose (
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(out)
        ]
    )