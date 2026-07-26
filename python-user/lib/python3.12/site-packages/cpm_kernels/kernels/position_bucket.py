from .base import Kernel, DevicePointer, CUDAStream
import ctypes

embedding_kernel = Kernel(
    "position_bucket",
    [
        "cu_init_position_mapping",
        "cu_position_embedding_forward",
        "cu_position_embedding_backward",
        "cu_position_embedding_step"
    ]
)

def position_embedding_init(
    num_buckets : int,
    max_distance : int,
    out : DevicePointer,    # (max_distance)    int32
    bidirectional : bool,
    stream : CUDAStream
):
    gridDim = (1, 1, 1)
    blockDim = (min(max_distance, 1024), 1, 1)
    embedding_kernel.cu_init_position_mapping(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(num_buckets),
            ctypes.c_int32(max_distance),
            ctypes.c_void_p(out),
            ctypes.c_bool(bidirectional)
        ]
    )

def position_embedding_forward(
    query_len : int,
    key_len : int,
    num_buckets : int,
    max_distance : int,
    num_heads : int,
    position_mapping : DevicePointer,   # (max_distance)
    weight : DevicePointer,             # (num_heads, num_bucket)
    out : DevicePointer,                # (num_heads, key_len, query_len)
    bidirectional : bool,
    stream : CUDAStream
):
    gridDim = (key_len, 1, 1)
    blockDim = (min(query_len, 1024), 1, 1)
    embedding_kernel.cu_position_embedding_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(query_len),
            ctypes.c_int32(key_len),
            ctypes.c_int32(num_buckets),
            ctypes.c_int32(max_distance),
            ctypes.c_int32(num_heads),
            ctypes.c_void_p(position_mapping),
            ctypes.c_void_p(weight),
            ctypes.c_void_p(out),
            ctypes.c_bool(bidirectional)
        ]
    )

def position_embedding_backward(
    query_len : int,
    key_len : int,
    num_buckets : int,
    max_distance : int,
    num_heads : int,    # no more than 1024
    position_mapping : DevicePointer,   # (max_distance)
    grad_out : DevicePointer,           # (num_heads, key_len, query_len)
    grad : DevicePointer,               # (num_heads, num_bucket)
    bidirectional : bool,
    stream : CUDAStream
):
    gridDim = (num_buckets, 1, 1)
    blockDim = (1024, 1, 1)
    embedding_kernel.cu_position_embedding_backward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(query_len),
            ctypes.c_int32(key_len),
            ctypes.c_int32(num_buckets),
            ctypes.c_int32(max_distance),
            ctypes.c_int32(num_heads),
            ctypes.c_void_p(position_mapping),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(grad),
            ctypes.c_bool(bidirectional)
        ]
    )

def position_embedding_step(
    query_pos : int,
    key_len : int,
    num_buckets : int,
    max_distance : int,
    num_heads : int,
    position_mapping : DevicePointer,   # (max_distance)
    weight : DevicePointer,             # (num_heads, num_bucket)
    out : DevicePointer,                # (num_heads, key_len)
    bidirectional : bool,
    stream : CUDAStream
):
    gridDim = (1, 1, 1)
    blockDim = (min(key_len, 1024), 1, 1)
    embedding_kernel.cu_position_embedding_step(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(query_pos),
            ctypes.c_int32(key_len),
            ctypes.c_int32(num_buckets),
            ctypes.c_int32(max_distance),
            ctypes.c_int32(num_heads),
            ctypes.c_void_p(position_mapping),
            ctypes.c_void_p(weight),
            ctypes.c_void_p(out),
            ctypes.c_bool(bidirectional)
        ]
    )