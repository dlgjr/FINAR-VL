import torch
from ..kernels import embedding_forward, embedding_backward_stage1, embedding_backward_stage2, transpose

class OpEmbedding(torch.autograd.Function):
    """
    Embedding function for the cpm_kernels.
    Input:
        - ids: (batch_size, seq_len)
        - weight: (vocab_size, embedding_size)
    Output:
        - embeddings: (batch_size, embedding_size, seq_len)
    """
    @staticmethod
    def forward(ctx, ids : torch.Tensor, weight : torch.Tensor):
        assert ids.is_cuda and weight.is_cuda
        assert ids.device == weight.device
        assert ids.ndim == 2
        assert weight.ndim == 2
        assert ids.dtype == torch.int32
        assert weight.dtype == torch.half
        if not ids.is_contiguous():
            ids = ids.contiguous()
        assert weight.is_contiguous()

        ctx.save_for_backward(ids, weight)

        out = torch.empty((ids.size(0), weight.size(1), ids.size(1)), device=ids.device, dtype=torch.half)
        assert out.is_contiguous()

        embedding_forward(ids.size(0), weight.size(1), ids.size(1), ids.data_ptr(), weight.data_ptr(), out.data_ptr(), torch.cuda.current_stream().cuda_stream)
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        ids, weight = ctx.saved_tensors
        batch, n, m = grad_output.size()

        assert grad_output.device == ids.device
        assert m == ids.size(1)
        assert n == weight.size(1)
        if not grad_output.is_contiguous():
            grad_output = grad_output.contiguous()

        sort_result = ids.view(-1).sort()
        indices = sort_result.indices.to(torch.int32)
        values = sort_result.values
        
        grad_transpose = torch.empty((batch, m, n), device=grad_output.device, dtype=torch.half)

        assert grad_output.is_contiguous() and grad_transpose.is_contiguous()
        transpose(batch, n, m, grad_output.data_ptr(), grad_transpose.data_ptr(), torch.cuda.current_stream().cuda_stream)

        buf = torch.empty((batch, n), device=grad_output.device, dtype=torch.half)
        buf_indices = torch.empty((batch,), device=grad_output.device, dtype=torch.int32)

        ret = torch.zeros((weight.size(0), n), device=grad_output.device, dtype=torch.half)
        assert grad_transpose.is_contiguous() and indices.is_contiguous() and values.is_contiguous() and ret.is_contiguous() and buf.is_contiguous() and buf_indices.is_contiguous()
        embedding_backward_stage1(
            batch, m, n,
            grad_transpose.data_ptr(),
            indices.data_ptr(),
            values.data_ptr(),
            ret.data_ptr(),
            buf.data_ptr(),
            buf_indices.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )

        embedding_backward_stage2(
            batch, n,
            buf.data_ptr(),
            buf_indices.data_ptr(),
            ret.data_ptr(),
            torch.cuda.current_stream().cuda_stream
        )

        return None, ret

class Embedding(torch.nn.Module):
    def __init__(self, vocab_size : int, embedding_size : int):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.empty((vocab_size, embedding_size), dtype=torch.half))

    def forward(self, ids : torch.Tensor):
        return OpEmbedding.apply(ids, self.weight)

class EmbeddingTH(torch.nn.Module):
    def __init__(self, vocab_size : int, embedding_size : int):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.empty((vocab_size, embedding_size), dtype=torch.half))

    def forward(self, ids : torch.Tensor):
        assert ids.ndim == 2
        v = torch.embedding(
            self.weight,
            ids
        )
        assert v.ndim == 3
        return v.transpose(1, 2)
