from .base import Kernel, DevicePointer, CUDAStream, round_up
from ..library import cublaslt
from ..device import current_device
import ctypes

gemv_kernel = Kernel(
    "gemv",
    [
        "cu_gemv_calc_scale",
        "cu_gemv_round",
        "cu_gemv_broadcast_mat_int8",
        "cu_gemv_fp16",
        "cu_gemv_fp16_transpose",
        "cu_gemv_broadcast_mat_fp16"
    ]
)

def gemv_calc_scale(
    batch : int, n : int,
    vec : DevicePointer,                # (batch, n)    fp16
    out : DevicePointer,                # (batch,)      fp16
    stream : CUDAStream
):
    gridDim = (batch, 1, 1)
    blockDim = (min(1024, round_up(n, 32)), 1, 1)
    gemv_kernel.cu_gemv_calc_scale(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(vec),
            ctypes.c_void_p(out)
        ]
    )

def gemv_round(
    batch : int, n : int,
    vec : DevicePointer,                # (batch, n)    fp16
    scale : DevicePointer,              # (batch)       fp16
    out : DevicePointer,                # (batch, n)    int8
    stream : CUDAStream
):
    threads = min(1024, round_up(n, 32))
    gridDim = (batch, round_up(n, threads) // threads, 1)
    blockDim = (threads, 1, 1)
    gemv_kernel.cu_gemv_round(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(n),
            ctypes.c_void_p(vec),
            ctypes.c_void_p(scale),
            ctypes.c_void_p(out)
        ]
    )


def gemv_broadcast_mat_int8(
    batch : int, dim_out : int, dim_in : int,
    scale_mat : DevicePointer,          # (dim_out,)    fp16
    mat : DevicePointer,                # (dim_out, dim_in) int8
    scale_vec : DevicePointer,          # (batch,)      fp16
    vec : DevicePointer,                # (batch, dim_in)   int8
    out : DevicePointer,                # (batch, dim_out)  fp16
    stream : CUDAStream
):
    assert dim_in % 4 == 0
    gridDim = (batch, dim_out, 1)
    blockDim = (min(1024, round_up(dim_in // 4, 32)), 1, 1)
    gemv_kernel.cu_gemv_broadcast_mat_int8(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(dim_out),
            ctypes.c_int32(dim_in),
            ctypes.c_void_p(scale_mat),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(scale_vec),
            ctypes.c_void_p(vec),
            ctypes.c_void_p(out)
        ]
    )


def gemv_fp16(
    batch : int, dim_out : int, dim_in : int,
    mat : DevicePointer,                # (batch, dim_out, dim_in) fp16
    vec : DevicePointer,                # (batch, dim_in)   fp16
    out : DevicePointer,                # (batch, dim_out)  fp16
    stream : CUDAStream
):
    device = current_device()
    device.use()
    layoutA = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_in, dim_out, dim_in)
    layoutB = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_in, 1, dim_in)
    layoutC = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_out, 1, dim_out)
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutA, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutA, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_in * dim_out))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutB, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutB, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_in))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutC, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutC, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_out))
    fallback_32f = device.architecture < 62

    if cublaslt.version >= 11000:
        if fallback_32f:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUBLAS_COMPUTE_32F, cublaslt.CUDA_R_32F)
        else:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUBLAS_COMPUTE_16F, cublaslt.CUDA_R_16F)
    else:
        if fallback_32f:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUDA_R_32F)
        else:    
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUDA_R_16F)
    cublaslt.cublasLtMatmulDescSetAttribute(matmulHandle, cublaslt.CUBLASLT_MATMUL_DESC_TRANSA, ctypes.c_int32(cublaslt.CUBLAS_OP_T))
    cublaslt.cublasLtMatmul(
        device.cublasLtHandle,
        matmulHandle,
        ctypes.c_float(1.0) if fallback_32f else ctypes.c_short(15360),  # half(1)
        mat, layoutA,
        vec, layoutB,
        ctypes.c_float(0) if fallback_32f else ctypes.c_short(0),      # half(0)
        out, layoutC,
        out, layoutC,
        stream
    )
    cublaslt.cublasLtMatmulDescDestroy(matmulHandle)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutA)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutB)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutC)

def gemv_fp16_light(
    batch : int, dim_out : int, dim_in : int,
    mat : DevicePointer,                # (batch, dim_out, dim_in) fp16
    vec : DevicePointer,                # (batch, dim_in)   fp16
    out : DevicePointer,                # (batch, dim_out)  fp16
    stream : CUDAStream
):
    assert dim_in % 2 == 0
    gridDim = (batch, dim_out, 1)
    blockDim = (min(1024, round_up(dim_in // 2, 32)), 1, 1)
    gemv_kernel.cu_gemv_fp16(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(dim_out),
            ctypes.c_int32(dim_in),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(vec),
            ctypes.c_void_p(out)
        ]
    )


def gemv_fp16_transpose(
    batch : int, dim_out : int, dim_in : int,
    mat : DevicePointer,                # (batch, dim_in, dim_out) fp16
    vec : DevicePointer,                # (batch, dim_in)   fp16
    out : DevicePointer,                # (batch, dim_out)  fp16
    stream : CUDAStream
):
    device = current_device()
    device.use()
    layoutA = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_out, dim_in, dim_out)
    layoutB = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_in, 1, dim_in)
    layoutC = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_out, 1, dim_out)
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutA, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutA, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_in * dim_out))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutB, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutB, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_in))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutC, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutC, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_out))

    fallback_32f = device.architecture < 62

    if cublaslt.version >= 11000:
        if fallback_32f:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUBLAS_COMPUTE_32F, cublaslt.CUDA_R_32F)
        else:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUBLAS_COMPUTE_16F, cublaslt.CUDA_R_16F)
    else:
        if fallback_32f:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUDA_R_32F)
        else:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUDA_R_16F)
    cublaslt.cublasLtMatmul(
        device.cublasLtHandle,
        matmulHandle,
        ctypes.c_float(1) if fallback_32f else ctypes.c_short(15360),  # half(1)
        mat, layoutA,
        vec, layoutB,
        ctypes.c_float(0) if fallback_32f else ctypes.c_short(0),      # half(0)
        out, layoutC,
        out, layoutC,
        stream
    )
    cublaslt.cublasLtMatmulDescDestroy(matmulHandle)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutA)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutB)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutC)

def gemv_fp16_transpose_light(
    batch : int, dim_out : int, dim_in : int,
    mat : DevicePointer,                # (batch, dim_in, dim_out) fp16
    vec : DevicePointer,                # (batch, dim_in)   fp16
    out : DevicePointer,                # (batch, dim_out)  fp16
    stream : CUDAStream
):
    gridDim = (batch, round_up(dim_out, 32) // 32, 1)
    blockDim = (32, 32, 1)
    gemv_kernel.cu_gemv_fp16_transpose(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(dim_out),
            ctypes.c_int32(dim_in),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(vec),
            ctypes.c_void_p(out)
        ]
    )

def gemv_broadcast_mat_fp16(
    batch : int, dim_out : int, dim_in : int,
    mat : DevicePointer,                # (dim_out, dim_in) fp16
    vec : DevicePointer,                # (batch, dim_in)
    out : DevicePointer,                # (batch, dim_out)
    stream : CUDAStream
):
    device = current_device()
    device.use()
    layoutA = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_in, dim_out, dim_in)
    layoutB = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_in, 1, dim_in)
    layoutC = cublaslt.cublasLtMatrixLayoutCreate(cublaslt.CUDA_R_16F, dim_out, 1, dim_out)
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutA, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutA, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(0))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutB, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutB, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_in))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutC, cublaslt.CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT, ctypes.c_int32(batch))
    cublaslt.cublasLtMatrixLayoutSetAttribute(layoutC, cublaslt.CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET, ctypes.c_int64(dim_out))
    fallback_32f = device.architecture < 62
    if cublaslt.version >= 11000:
        if fallback_32f:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUBLAS_COMPUTE_32F, cublaslt.CUDA_R_32F)
        else:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUBLAS_COMPUTE_16F, cublaslt.CUDA_R_16F)
    else:
        if fallback_32f:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUDA_R_32F)
        else:
            matmulHandle = cublaslt.cublasLtMatmulDescCreate(cublaslt.CUDA_R_16F)
    cublaslt.cublasLtMatmulDescSetAttribute(matmulHandle, cublaslt.CUBLASLT_MATMUL_DESC_TRANSA, ctypes.c_int32(cublaslt.CUBLAS_OP_T))
    cublaslt.cublasLtMatmul(
        device.cublasLtHandle,
        matmulHandle,
        ctypes.c_float(1) if fallback_32f else ctypes.c_short(15360),  # half(1)
        mat, layoutA,
        vec, layoutB,
        ctypes.c_float(0) if fallback_32f else ctypes.c_short(0),      # half(0)
        out, layoutC,
        out, layoutC,
        stream
    )
    cublaslt.cublasLtMatmulDescDestroy(matmulHandle)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutA)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutB)
    cublaslt.cublasLtMatrixLayoutDestroy(layoutC)

def gemv_broadcast_mat_fp16_light(
    batch : int, dim_out : int, dim_in : int,
    mat : DevicePointer,                # (dim_out, dim_in) fp16
    vec : DevicePointer,                # (batch, dim_in)
    out : DevicePointer,                # (batch, dim_out)
    stream : CUDAStream
):
    assert dim_in % 2 == 0
    gridDim = (batch, dim_out, 1)
    blockDim = (min(1024, round_up(dim_in // 2, 32)), 1, 1)
    gemv_kernel.cu_gemv_broadcast_mat_fp16(
        gridDim, blockDim, 0, stream, [
            ctypes.c_int32(batch),
            ctypes.c_int32(dim_out),
            ctypes.c_int32(dim_in),
            ctypes.c_void_p(mat),
            ctypes.c_void_p(vec),
            ctypes.c_void_p(out)
        ]
    )
