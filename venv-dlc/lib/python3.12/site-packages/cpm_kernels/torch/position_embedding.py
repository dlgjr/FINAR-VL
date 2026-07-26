import torch
from ..kernels import position_embedding_init, position_embedding_forward, position_embedding_backward
import math
import torch.nn.functional as F

class OpPositionEmbedding(torch.autograd.Function):
    @staticmethod
    def forward(ctx, query_len, key_len, num_buckets, max_distance, num_heads, weight : torch.Tensor, bidirectional : bool):
        assert weight.is_cuda and weight.is_contiguous() and weight.dtype == torch.float16
        device = weight.device

        mapping = torch.empty( (max_distance,), dtype=torch.int32, device=device )
        position_embedding_init(
            num_buckets,
            max_distance,
            mapping.data_ptr(),
            bidirectional,
            torch.cuda.current_stream().cuda_stream
        )
        out = torch.empty((num_heads, key_len, query_len), device=device, dtype=torch.float16)
        position_embedding_forward(
            query_len,
            key_len,
            num_buckets,
            max_distance,
            num_heads,
            mapping.data_ptr(),
            weight.data_ptr(),
            out.data_ptr(),
            bidirectional,
            torch.cuda.current_stream().cuda_stream
        )
        ctx.save_for_backward(mapping)
        ctx.input_args = (query_len, key_len, num_buckets, max_distance, num_heads, bidirectional)
        return out
    
    @staticmethod
    def backward(ctx, grad_output : torch.Tensor):
        assert grad_output.is_cuda and grad_output.is_contiguous() and grad_output.dtype == torch.float16
        query_len, key_len, num_buckets, max_distance, num_heads, bidirectional = ctx.input_args
        mapping = ctx.saved_tensors[0]
        grad = torch.empty((num_heads, num_buckets), device=grad_output.device, dtype=torch.float16)
        position_embedding_backward(
            query_len,
            key_len,
            num_buckets,
            max_distance,
            num_heads,
            mapping.data_ptr(),
            grad_output.data_ptr(),
            grad.data_ptr(),
            bidirectional,
            torch.cuda.current_stream().cuda_stream
        )
        return None, None, None, None, None, grad, None

class PositionEmbedding(torch.nn.Module):
    def __init__(self, num_heads, num_buckets, max_distance, bidirectional=True):
        super(PositionEmbedding, self).__init__()
        self.weight = torch.nn.Parameter(torch.randn(num_heads, num_buckets))

        self.num_heads = num_heads
        self.num_buckets = num_buckets
        self.max_distance = max_distance
        self.bidirectional = bidirectional


    def forward(self, key_len, query_len):
        return OpPositionEmbedding.apply(query_len, key_len, self.num_buckets, self.max_distance, self.num_heads, self.weight, self.bidirectional)



class PositionEmbeddingTH(torch.nn.Module):
    def __init__(self, num_heads, num_buckets, max_distance, bidirectional=True) -> None:
        super(PositionEmbeddingTH, self).__init__()
        self.num_buckets = num_buckets
        self.num_heads = num_heads
        self.max_distance = max_distance
        self.bidirectional = bidirectional

        # self.embedding = weight(self.num_buckets, self.num_heads)
        self.weight = torch.nn.Parameter(torch.randn(num_heads, num_buckets))

    def relative_position_bucket(self, relative_position, bidirectional=True, num_buckets=32, max_distance=128):
        relative_buckets = 0
        if bidirectional:
            num_buckets //= 2
            relative_buckets += (relative_position > 0).to(torch.long) * num_buckets
            relative_position = torch.abs(relative_position)
        else:
            relative_position = -torch.min(relative_position, torch.zeros_like(relative_position))
        # now relative_position is in the range [0, inf)

        # half of the buckets are for exact increments in positions
        max_exact = num_buckets // 2
        is_small = relative_position < max_exact

        # The other half of the buckets are for logarithmically bigger bins in positions up to max_distance
        relative_postion_if_large = max_exact + (
            torch.log(relative_position.float() / max_exact)
            / math.log(max_distance / max_exact)
            * (num_buckets - max_exact)
        ).to(torch.long)
        relative_postion_if_large = torch.min(
            relative_postion_if_large, torch.full_like(relative_postion_if_large, num_buckets - 1)
        )

        relative_buckets += torch.where(is_small, relative_position, relative_postion_if_large)
        return relative_buckets

    def compute_bias(self, query_length, key_length):
        """ Compute binned relative position bias """
        device = self.weight.device
        context_position = torch.arange(query_length, dtype=torch.long, device=device)[:, None]
        memory_position = torch.arange(key_length, dtype=torch.long, device=device)[None, :]
        relative_position = memory_position - context_position  # shape (query_length, key_length)
        relative_position_bucket = self.relative_position_bucket(
            relative_position,
            bidirectional=self.bidirectional,
            num_buckets=self.num_buckets,
            max_distance=self.max_distance,
        )
        values = F.embedding(relative_position_bucket, self.weight.transpose(0, 1))
        values = values.permute([2, 1, 0]) # shape (num_heads, key_length, query_length)
        return values
    
    def forward(self, key_length, query_length):
        return self.compute_bias(query_length, key_length)
