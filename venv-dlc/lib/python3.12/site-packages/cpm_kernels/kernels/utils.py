from ..library import cublaslt
from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

utils_kernel = Kernel(
    "utils",
    [
        "copy_data_to_kv",
        "cu_array_add",
        "cu_adjustify_logits",
        "cu_copy_extend_buffer",
        "cu_has_nan_inf",
        "cu_copy_pos_hidden"
    ]
)


def copy_data_to_kv(
    batch : int, buffer_len : int, n : int,
    inp : DevicePointer,        # (batch, n)
    out : DevicePointer,        # (batch, buffer_len, n)
    pos : int,
    stream : CUDAStream
):
    assert n % 2 == 0
    gridDim = (batch, 1, 1)
    blockDim = (min(1024, n // 2), 1, 1)
    utils_kernel.copy_data_to_kv(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(buffer_len),
            ctypes.c_int32(n),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(out),
            ctypes.c_int32(pos)
        ]
    )

def array_add(
    array : DevicePointer,
    pos : int,
    val : int,
    stream : CUDAStream
):
    gridDim = (1, 1, 1)
    blockDim = (1, 1, 1)
    utils_kernel.cu_array_add(
        gridDim, blockDim, 0, stream, [
            ctypes.c_void_p(array),
            ctypes.c_int32(pos),
            ctypes.c_int32(val)
        ]
    )

def adjustify_logits(
    batch : int, n : int,
    logits : DevicePointer,
    temperature : float,
    frequency_penalty : float,
    presence_penalty : float,
    frequency : DevicePointer,
    stream : CUDAStream
):
    threads = min(1024, round_up(n, 32))
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    utils_kernel.cu_adjustify_logits(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(logits),
            ctypes.c_float(temperature),
            ctypes.c_float(frequency_penalty),
            ctypes.c_float(presence_penalty),
            ctypes.c_void_p(frequency)
        ]
    )

def copy_extend_buffer(
    batch : int, old_size : int, nw_size : int,
    old_buffer : DevicePointer,
    new_buffer : DevicePointer,
    stream : CUDAStream
):
    threads = min(1024, round_up(old_size, 32))
    gridDim = (batch, round_up(old_size, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    utils_kernel.cu_copy_extend_buffer(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(old_size),
            ctypes.c_int32(nw_size),
            ctypes.c_void_p(old_buffer),
            ctypes.c_void_p(new_buffer)
        ]
    )

def has_nan_inf(
    n : int,
    inp : DevicePointer,    # (n,)  half
    out : DevicePointer,    # (1,)  bool
    stream : CUDAStream
):
    gridDim = (1, 1, 1)
    blockDim = (min(round_up(n, 32), 1024), 1, 1)
    utils_kernel.cu_has_nan_inf(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(n),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(out)
        ]
    )

def copy_pos_hidden(
    batch : int, hidden_size : int, seq_len : int,
    pos : int,
    inp : DevicePointer,    # (batch, hidden_size, seq_len)
    out : DevicePointer,    # (batch, hidden_size)
    stream : CUDAStream
):
    threads = min(1024, round_up(hidden_size, 32))
    gridDim = (batch, round_up(hidden_size, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    utils_kernel.cu_copy_pos_hidden(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(hidden_size),
            ctypes.c_int32(seq_len),
            ctypes.c_int32(pos),
            ctypes.c_void_p(inp),
            ctypes.c_void_p(out)
        ]
    )