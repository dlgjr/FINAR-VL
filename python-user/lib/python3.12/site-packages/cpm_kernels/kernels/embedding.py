from .base import Kernel, DevicePointer, CUDAStream, round_up
import ctypes

embedding_kernel = Kernel(
    "embedding",
    [
        "cu_embedding_forward",
        "cu_embedding_backward_stage1",
        "cu_embedding_backward_stage2",
        "cu_embedding_step"
    ]
)

def embedding_forward(
    batch : int, 
    hidden_size : int,          # hidden size
    seq_len : int,              # sequence length
    ids : DevicePointer,        # (batch, m)
    weights : DevicePointer,    # (vocab_size, n)
    out : DevicePointer,        # (batch, n, m)
    stream : CUDAStream
):
    gridDim = (batch, round_up(seq_len, 32) // 32, round_up(hidden_size, 32) // 32)
    blockDim = (32, 32, 1)
    embedding_kernel.cu_embedding_forward(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(hidden_size),
            ctypes.c_int32(seq_len),
            ctypes.c_void_p(ids),
            ctypes.c_void_p(weights),
            ctypes.c_void_p(out)
        ]
    )

def embedding_backward_stage1(
        batch : int, 
        seq_len : int, 
        hidden_size : int,
        grad_out : DevicePointer,       # (batch * n, m)
        argsort_ids : DevicePointer,    # (batch, n)
        sorted_ids : DevicePointer,     # (batch, n)
        grad : DevicePointer,           # (vocab_size, m)
        aux_grad : DevicePointer,       # (batch, m)
        aux_grad_idx : DevicePointer,   # (batch)
        stream : CUDAStream
    ):
    """
    Sort idx and calc grad stage1
    """
    gridDim = (batch, round_up(hidden_size, 1024) // 1024, 1)
    blockDim = (1024, 1, 1)
    embedding_kernel.cu_embedding_backward_stage1(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(seq_len),
            ctypes.c_int32(hidden_size),
            ctypes.c_void_p(grad_out),
            ctypes.c_void_p(argsort_ids),
            ctypes.c_void_p(sorted_ids),
            ctypes.c_void_p(grad),
            ctypes.c_void_p(aux_grad),
            ctypes.c_void_p(aux_grad_idx)
        ]
    )

def embedding_backward_stage2(
        batch : int,
        hidden_size : int,
        aux_grad : DevicePointer,       # (batch, m)
        aux_grad_idx : DevicePointer,   # (batch)
        grad : DevicePointer,           # (vocab_size, m)
        stream : CUDAStream
    ):

    gridDim = (round_up(hidden_size, 1024) // 1024, 1, 1)
    blockDim = (1024, 1, 1)
    embedding_kernel.cu_embedding_backward_stage2(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(hidden_size),
            ctypes.c_void_p(aux_grad),
            ctypes.c_void_p(aux_grad_idx),
            ctypes.c_void_p(grad)
        ]
    )

def embedding_step(
        batch : int, embedding_size : int,
        ids : DevicePointer,            # (batch,)  int32
        weights : DevicePointer,        # (vocab_size, embedding_size)  fp16
        out : DevicePointer,            # (batch, embedding_size)  fp16
        stream : CUDAStream
    ):
    gridDim = (batch, 1, 1)
    blockDim = (min(1024, embedding_size), 1, 1)
    embedding_kernel.cu_embedding_step(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(embedding_size),
            ctypes.c_void_p(ids),
            ctypes.c_void_p(weights),
            ctypes.c_void_p(out)
        ]
    )