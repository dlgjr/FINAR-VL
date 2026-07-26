from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes


mask_kernel = Kernel(
    "mask",
    [
        "cu_mask"
    ]
)

def mask(
        batch : int, n : int, m : int,
        inp : DevicePointer,    # (batch, n, m)
        mask : DevicePointer,   # (batch, m)
        value : float,
        out : DevicePointer,    # (batch, n, m)
        stream : CUDAStream
    ):
    """
    mask
    """
    gridDim = (batch, round_up(m, 1024) // 1024, 1)
    blockDim = (min(m, 1024), 1, 1)
    mask_kernel.cu_mask(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_int32(m),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(mask),
            ctypes.c_float(value),
            ctypes.c_void_p(out)
        ]
    )
