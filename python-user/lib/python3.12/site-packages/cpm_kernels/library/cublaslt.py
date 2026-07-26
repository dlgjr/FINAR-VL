import ctypes
from typing import Any, List, Tuple
from .base import Lib

cublasLt = Lib("cublasLt")

CUDA_R_8I = 3
CUDA_R_32I = 10
CUDA_R_16F = 2
CUDA_R_32F = 0

CUBLAS_OP_N = 0
CUBLAS_OP_T = 1

CUBLASLT_ORDER_COL = 0
CUBLASLT_ORDER_ROW = 1
CUBLASLT_ORDER_COL32 = 2
CUBLASLT_ORDER_COL4_4R2_8C = 3
CUBLASLT_ORDER_COL32_2R_4R4 = 4


CUBLASLT_MATRIX_LAYOUT_TYPE = 0
CUBLASLT_MATRIX_LAYOUT_ORDER = 1
CUBLASLT_MATRIX_LAYOUT_ROWS = 2
CUBLASLT_MATRIX_LAYOUT_COLS = 3
CUBLASLT_MATRIX_LAYOUT_LD = 4
CUBLASLT_MATRIX_LAYOUT_BATCH_COUNT = 5
CUBLASLT_MATRIX_LAYOUT_STRIDED_BATCH_OFFSET = 6
CUBLASLT_MATRIX_LAYOUT_PLANE_OFFSET = 7

CUBLASLT_MATMUL_DESC_COMPUTE_TYPE = 0
CUBLASLT_MATMUL_DESC_SCALE_TYPE = 1
CUBLASLT_MATMUL_DESC_POINTER_MODE = 2
CUBLASLT_MATMUL_DESC_TRANSA = 3
CUBLASLT_MATMUL_DESC_TRANSB = 4
CUBLASLT_MATMUL_DESC_TRANSC = 5
CUBLASLT_MATMUL_DESC_FILL_MODE = 6
CUBLASLT_MATMUL_DESC_EPILOGUE = 7
CUBLASLT_MATMUL_DESC_BIAS_POINTER = 8

CUBLASLT_MATRIX_TRANSFORM_DESC_SCALE_TYPE = 0
CUBLASLT_MATRIX_TRANSFORM_DESC_POINTER_MODE = 1
CUBLASLT_MATRIX_TRANSFORM_DESC_TRANSA = 2
CUBLASLT_MATRIX_TRANSFORM_DESC_TRANSB = 3

CUBLAS_COMPUTE_16F               = 64
CUBLAS_COMPUTE_16F_PEDANTIC      = 65
CUBLAS_COMPUTE_32F               = 68
CUBLAS_COMPUTE_32F_PEDANTIC      = 69
CUBLAS_COMPUTE_32F_FAST_16F      = 74
CUBLAS_COMPUTE_32F_FAST_16BF     = 75
CUBLAS_COMPUTE_32F_FAST_TF32     = 77
CUBLAS_COMPUTE_64F               = 70
CUBLAS_COMPUTE_64F_PEDANTIC      = 71
CUBLAS_COMPUTE_32I               = 72
CUBLAS_COMPUTE_32I_PEDANTIC      = 73

cublasLtHandle_t = ctypes.c_void_p
cublasStatus_t = ctypes.c_int
cublasLtMatrixTransformDesc_t = ctypes.c_void_p
cudaStream_t = ctypes.c_void_p
cublasLtMatmulDesc_t = ctypes.c_void_p
cublasLtMatrixLayout_t = ctypes.c_void_p
cudaDataType = ctypes.c_int
cublasComputeType_t = ctypes.c_int
cublasLtMatmulDescAttributes_t = ctypes.c_int
cublasLtMatrixLayoutAttribute_t = ctypes.c_int
cublasLtMatrixTransformDescAttributes_t = ctypes.c_int

@cublasLt.bind("cublasLtGetVersion", [], ctypes.c_size_t)
def cublasLtGetVersion() -> int:
    return cublasLt.cublasLtGetVersion()

try:
    version = cublasLtGetVersion()
except RuntimeError:
    version = 0

def cublasGetStatusString(status : int) -> str:
    cublas_errors = {
        0: "CUBLAS_STATUS_SUCCESS",
        1: "CUBLAS_STATUS_NOT_INITIALIZED",
        3: "CUBLAS_STATUS_ALLOC_FAILED",
        7: "CUBLAS_STATUS_INVALID_VALUE",
        8: "CUBLAS_STATUS_ARCH_MISMATCH",
        11: "CUBLAS_STATUS_MAPPING_ERROR",
        13: "CUBLAS_STATUS_EXECUTION_FAILED",
        14: "CUBLAS_STATUS_INTERNAL_ERROR",
        15: "CUBLAS_STATUS_NOT_SUPPORTED",
        16: "CUBLAS_STATUS_LICENSE_ERROR"
    }
    if status not in cublas_errors:
        raise RuntimeError("Unknown cublasLt status: %d" % status)
    return cublas_errors[status]

def checkCublasStatus(status: int) -> None:
    if status != 0:
        raise RuntimeError("CUBLAS error: {}".format(
            cublasGetStatusString(status)
        ))

@cublasLt.bind("cublasLtCreate", [ctypes.POINTER(cublasLtHandle_t)], cublasStatus_t)
def cublasLtCreate() -> cublasLtHandle_t:
    handle = cublasLtHandle_t()
    checkCublasStatus(cublasLt.cublasLtCreate(ctypes.byref(handle)))
    return handle

@cublasLt.bind("cublasLtDestroy", [cublasLtHandle_t], cublasStatus_t)
def cublasLtDestroy(handle: cublasLtHandle_t) -> None:
    checkCublasStatus(cublasLt.cublasLtDestroy(handle))


@cublasLt.bind("cublasLtMatmul", [
    cublasLtHandle_t, cublasLtMatmulDesc_t, 
    ctypes.c_void_p, 
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    ctypes.c_void_p, 
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    cudaStream_t
], cublasStatus_t)
def cublasLtMatmul(
        lightHandle : cublasLtHandle_t,
        computeDesc : cublasLtMatmulDesc_t,
        alpha : Any,
        A : ctypes.c_void_p, A_layout : cublasLtMatrixLayout_t,
        B : ctypes.c_void_p, B_layout : cublasLtMatrixLayout_t,
        beta : Any,
        C : ctypes.c_void_p, C_layout : cublasLtMatrixLayout_t,
        D : ctypes.c_void_p, D_layout : cublasLtMatrixLayout_t,
        stream : cudaStream_t
    ) -> None:
    checkCublasStatus(cublasLt.cublasLtMatmul(
        lightHandle,
        computeDesc,
        ctypes.byref(alpha),
        A, A_layout,
        B, B_layout,
        ctypes.byref(beta),
        C, C_layout,
        D, D_layout,
        0,
        0,
        0,
        stream
    ))


if version >= 11000:
    @cublasLt.bind("cublasLtMatmulDescCreate", [ctypes.POINTER(cublasLtMatmulDesc_t), cublasComputeType_t, cudaDataType], cublasStatus_t)
    def cublasLtMatmulDescCreate(computeType : cublasComputeType_t, dataType : cudaDataType) -> cublasLtMatmulDesc_t:
        desc = cublasLtMatmulDesc_t()
        checkCublasStatus(cublasLt.cublasLtMatmulDescCreate(ctypes.byref(desc), computeType, dataType))
        return desc

else:
    @cublasLt.bind("cublasLtMatmulDescCreate", [ctypes.POINTER(cublasLtMatmulDesc_t), cudaDataType], cublasStatus_t)
    def cublasLtMatmulDescCreate(computeType : cudaDataType) -> cublasLtMatmulDesc_t:
        desc = cublasLtMatmulDesc_t()
        checkCublasStatus(cublasLt.cublasLtMatmulDescCreate(ctypes.byref(desc), computeType))
        return desc

@cublasLt.bind("cublasLtMatmulDescSetAttribute", [cublasLtMatmulDesc_t, cublasLtMatmulDescAttributes_t, ctypes.c_void_p, ctypes.c_size_t], cublasStatus_t)
def cublasLtMatmulDescSetAttribute(desc : cublasLtMatmulDesc_t, attr : cublasLtMatmulDescAttributes_t, value : Any) -> None:
    checkCublasStatus(cublasLt.cublasLtMatmulDescSetAttribute(desc, attr, ctypes.byref(value), ctypes.sizeof(value)))

@cublasLt.bind("cublasLtMatmulDescDestroy", [cublasLtMatmulDesc_t], cublasStatus_t)
def cublasLtMatmulDescDestroy(desc : cublasLtMatmulDesc_t) -> None:
    checkCublasStatus(cublasLt.cublasLtMatmulDescDestroy(desc))

@cublasLt.bind("cublasLtMatrixLayoutCreate", [ctypes.POINTER(cublasLtMatrixLayout_t), cudaDataType, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int64], cublasStatus_t)
def cublasLtMatrixLayoutCreate(dataType : cudaDataType, rows : int, cols : int, ld : int) -> cublasLtMatrixLayout_t:
    layout = cublasLtMatrixLayout_t()
    checkCublasStatus(cublasLt.cublasLtMatrixLayoutCreate(ctypes.byref(layout), dataType, rows, cols, ld))
    return layout

@cublasLt.bind("cublasLtMatrixLayoutDestroy", [cublasLtMatrixLayout_t], cublasStatus_t)
def cublasLtMatrixLayoutDestroy(layout : cublasLtMatrixLayout_t) -> None:
    checkCublasStatus(cublasLt.cublasLtMatrixLayoutDestroy(layout))

@cublasLt.bind("cublasLtMatrixLayoutSetAttribute", [cublasLtMatrixLayout_t, cublasLtMatrixLayoutAttribute_t, ctypes.c_void_p, ctypes.c_size_t], cublasStatus_t)
def cublasLtMatrixLayoutSetAttribute(layout : cublasLtMatrixLayout_t, attr : cublasLtMatrixLayoutAttribute_t, value : Any) -> None:
    checkCublasStatus(cublasLt.cublasLtMatrixLayoutSetAttribute(layout, attr, ctypes.byref(value), ctypes.sizeof(value)))

@cublasLt.bind("cublasLtMatrixTransform", [
    cublasLtHandle_t, cublasLtMatrixTransformDesc_t, 
    ctypes.c_void_p,
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    ctypes.c_void_p,
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    ctypes.c_void_p, cublasLtMatrixLayout_t,
    cudaStream_t
], cublasStatus_t)
def cublasLtMatrixTransform(
        lightHandle : cublasLtHandle_t,
        transformDesc : cublasLtMatrixTransformDesc_t,
        alpha : Any,
        A : ctypes.c_void_p, A_layout : cublasLtMatrixLayout_t,
        beta : Any,
        B : ctypes.c_void_p, B_layout : cublasLtMatrixLayout_t,
        C : ctypes.c_void_p, C_layout : cublasLtMatrixLayout_t,
        stream : cudaStream_t
    ) -> None:
    checkCublasStatus(cublasLt.cublasLtMatrixTransform(
        lightHandle,
        transformDesc,
        ctypes.byref(alpha),
        A, A_layout,
        ctypes.byref(beta),
        B, B_layout,
        C, C_layout,
        stream
    ))

@cublasLt.bind("cublasLtMatrixTransformDescCreate", [ctypes.POINTER(cublasLtMatrixTransformDesc_t), cudaDataType], cublasStatus_t)
def cublasLtMatrixTransformDescCreate(dataType : cudaDataType) -> cublasLtMatrixTransformDesc_t:
    desc = cublasLtMatrixTransformDesc_t()
    checkCublasStatus(cublasLt.cublasLtMatrixTransformDescCreate(ctypes.byref(desc), dataType))
    return desc

@cublasLt.bind("cublasLtMatrixTransformDescDestroy", [cublasLtMatrixTransformDesc_t], cublasStatus_t)
def cublasLtMatrixTransformDescDestroy(desc : cublasLtMatrixTransformDesc_t) -> None:
    checkCublasStatus(cublasLt.cublasLtMatrixTransformDescDestroy(desc))

@cublasLt.bind("cublasLtMatrixTransformDescSetAttribute", [cublasLtMatrixTransformDesc_t, cublasLtMatrixTransformDescAttributes_t, ctypes.c_void_p, ctypes.c_size_t], cublasStatus_t)
def cublasLtMatrixTransformDescSetAttribute(desc : cublasLtMatrixTransformDesc_t, attr : cublasLtMatrixTransformDescAttributes_t, value : Any) -> None:
    checkCublasStatus(cublasLt.cublasLtMatrixTransformDescSetAttribute(desc, attr, ctypes.byref(value), ctypes.sizeof(value)))
