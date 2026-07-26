from typing import Optional
import torch
from ..kernels import gemm_calc_scale, gemm_calc_scale_transpose, gemm_round, gemm_round_transpose, gemm_scale, gemm_fp16, gemm_int8, gemm_backward_round_scale, gemm_backward_scale_round, gemm_scale_x, gemm_scale_y

def calc_scale(mat : torch.Tensor, transpose : bool):
    assert mat.is_contiguous() and mat.is_cuda
    if transpose:
        out = torch.empty((mat.size(0), mat.size(2)), dtype=torch.half, device=mat.device)
        gemm_calc_scale_transpose(
            mat.size(0), mat.size(1), mat.size(2),
            mat.data_ptr(), out.data_ptr(), torch.cuda.current_stream().cuda_stream
        )
    else:
        out = torch.empty((mat.size(0), mat.size(1)), dtype=torch.half, device=mat.device)
        gemm_calc_scale(
            mat.size(0), mat.size(1), mat.size(2),
            mat.data_ptr(), out.data_ptr(), torch.cuda.current_stream().cuda_stream
        )
    return out

def round_i8(mat : torch.Tensor, scale : torch.Tensor, transpose : bool):
    assert mat.is_contiguous() and mat.is_cuda
    assert scale.is_contiguous() and scale.is_cuda
    if transpose:
        out = torch.empty(mat.size(), dtype=torch.int8, device=mat.device)
        gemm_round_transpose(
            mat.size(0), mat.size(1), mat.size(2),
            mat.data_ptr(), scale.data_ptr(), out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
    else:
        out = torch.empty(mat.size(), dtype=torch.int8, device=mat.device)
        gemm_round(
            mat.size(0), mat.size(1), mat.size(2),
            mat.data_ptr(), scale.data_ptr(), out.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
    return out

def gemm_and_scale(quantA : torch.Tensor, scaleA : Optional[torch.Tensor], quantB : torch.Tensor, scaleB : Optional[torch.Tensor], aT, bT) -> torch.Tensor:
    M = quantA.size(2) if aT else quantA.size(1)
    K = quantA.size(1) if aT else quantA.size(2)
    N = quantB.size(1) if bT else quantB.size(2)
    result_i32 = torch.empty((max(quantA.size(0), quantB.size(0)), M, N), dtype=torch.int32, device=quantA.device)
    gemm_int8 (
        N, K, M,
        quantB.size(0), quantA.size(0),
        bT, aT,
        quantB.data_ptr(), quantA.data_ptr(),
        result_i32.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )
    result_fp = torch.empty((max(quantA.size(0), quantB.size(0)), M, N), dtype=torch.float16, device=quantA.device)

    if scaleA is not None and scaleB is not None:
        gemm_scale(
            result_i32.size(0), M, N, 
            result_i32.data_ptr(), 
            scaleA.data_ptr(), scaleB.data_ptr(), 
            result_fp.data_ptr(),
            quantA.size(0) == 1,
            quantB.size(0) == 1,
            torch.cuda.current_stream().cuda_stream
        )
    elif scaleA is not None:
        gemm_scale_x(
            result_i32.size(0), M, N,
            result_i32.data_ptr(),
            scaleA.data_ptr(),
            result_fp.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
    else:
        assert scaleB is not None
        gemm_scale_y(
            result_i32.size(0), M, N,
            result_i32.data_ptr(),
            scaleB.data_ptr(),
            result_fp.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )
    return result_fp

class GEMMInt8(torch.autograd.Function):
    @staticmethod
    def forward(ctx, A : torch.Tensor, aT : bool, B : torch.Tensor, bT : bool):
        """
        Input:
          - A:  (batchA, M, K)
          - B:  (batchB, K, N)
        Output:
          - C:  (batch, M, N)
        """
        assert A.is_cuda and B.is_cuda and A.device == B.device
        assert A.is_contiguous() and B.is_contiguous()
        assert A.dtype == torch.half and B.dtype == torch.half

        scale_A = calc_scale(A, aT)
        scale_B = calc_scale(B, not bT)

        quantized_A = round_i8(A, scale_A, aT)
        quantized_B = round_i8(B, scale_B, not bT)

        result = gemm_and_scale(quantized_A, scale_A, quantized_B, scale_B, aT, bT)

        # save backward
        ctx.save_for_backward(
            scale_A, quantized_A,
            scale_B, quantized_B
        )
        ctx.aT = aT
        ctx.bT = bT
        return result

    @staticmethod
    def backward(ctx, grad_f : torch.Tensor):
        assert grad_f.is_contiguous() and grad_f.is_cuda and grad_f.dtype == torch.float16
        scale_A, quantized_A, scale_B, quantized_B = ctx.saved_tensors
        aT, bT = ctx.aT, ctx.bT

        batch, m, n = grad_f.size()
        
        scale_G_a = torch.empty((batch, m), dtype=torch.half, device=grad_f.device)
        quant_G_a = torch.empty((batch, m, n), dtype=torch.int8, device=grad_f.device)
        gemm_backward_round_scale(
            batch, m, n,
            grad_f.data_ptr(),
            scale_B.data_ptr(),
            quant_G_a.data_ptr(),
            scale_G_a.data_ptr(),
            scale_B.size(0) == 1,
            torch.cuda.current_stream().cuda_stream
        )

        if aT:
            grad_A = gemm_and_scale(
                quantized_B, None,
                quant_G_a, scale_G_a,
                bT, True
            )
        else:
            grad_A = gemm_and_scale(
                quant_G_a, scale_G_a,
                quantized_B, None,
                False, not bT
            )
        del scale_G_a
        del quant_G_a

        scale_G_b = torch.empty((batch, n), dtype=torch.half, device=grad_f.device)
        quant_G_b = torch.empty((batch, m, n), dtype=torch.int8, device=grad_f.device)
        gemm_backward_scale_round(
            batch, m, n,
            grad_f.data_ptr(),
            scale_A.data_ptr(),
            quant_G_b.data_ptr(),
            scale_G_b.data_ptr(),
            scale_A.size(0) == 1,
            torch.cuda.current_stream().cuda_stream
        )
        if bT:
            grad_B = gemm_and_scale(
                quant_G_b, scale_G_b,
                quantized_A, None,
                True, aT
            )
        else:
            grad_B = gemm_and_scale(
                quantized_A, None,
                quant_G_b, scale_G_b,
                not aT, False
            )

        if scale_A.size(0) == 1 and grad_A.size(0) > 1:
            grad_A = grad_A.sum(dim=0, keepdim=True)
        if scale_B.size(0) == 1 and grad_B.size(0) > 1:
            grad_B = grad_B.sum(dim=0, keepdim=True)
    
        return grad_A, None, grad_B, None 
        

def gemm_pth_fp16(A : torch.Tensor, aT : bool, B : torch.Tensor,bT : bool) -> torch.Tensor:
    M = A.size(2) if aT else A.size(1)
    K = A.size(1) if aT else A.size(2)
    N = B.size(1) if bT else B.size(2)
    out = torch.empty((max(A.size(0), B.size(0)), M, N), dtype=torch.float16, device=A.device)
    gemm_fp16(
        N, K, M,
        B.size(0), A.size(0),
        bT, aT,
        B.data_ptr(), A.data_ptr(),
        out.data_ptr(),
        torch.cuda.current_stream().cuda_stream
    )
    return out

class GEMMFloat(torch.autograd.Function):
    @staticmethod
    def forward(ctx, A : torch.Tensor, aT, B : torch.Tensor, bT):
        assert A.is_cuda and A.is_contiguous() and A.dtype == torch.half 
        assert B.is_cuda and B.is_contiguous() and B.dtype == torch.half
        assert A.device == B.device

        ctx.save_for_backward(A, B)
        ctx.aT = aT
        ctx.bT = bT

        return gemm_pth_fp16(A, aT, B, bT)

    @staticmethod
    def backward(ctx, grad_f):
        assert grad_f.is_cuda and grad_f.is_contiguous() and grad_f.dtype == torch.float16
        aT = ctx.aT
        bT = ctx.bT
        A, B = ctx.saved_tensors
        if aT:
            grad_A = gemm_pth_fp16(B, bT, grad_f, True)
        else:
            grad_A = gemm_pth_fp16(grad_f, False, B, not bT)
        
        if bT:
            grad_B = gemm_pth_fp16(grad_f, True, A, aT)
        else:
            grad_B = gemm_pth_fp16(A, not aT, grad_f, False)
        
        if A.size(0) == 1 and grad_A.size(0) > 1:
            grad_A = grad_A.sum(dim=0, keepdim=True)
        if B.size(0) == 1 and grad_B.size(0) > 1:
            grad_B = grad_B.sum(dim=0, keepdim=True)

        return grad_A, None, grad_B, None 

def bmm(A : torch.Tensor, aT : bool, B : torch.Tensor, bT : bool, int8 : bool =False) -> torch.Tensor:
    assert A.ndim == 3
    assert B.ndim == 3
    if int8:
        return GEMMInt8.apply(A, aT, B, bT)
    else:
        return GEMMFloat.apply(A, aT, B, bT)
