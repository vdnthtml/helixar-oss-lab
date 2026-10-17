import hashlib
import math
from typing import Dict, List, Optional

from mem0.embeddings.base import EmbeddingBase
from mem0.llms.base import LLMBase


class DeterministicEmbedding(EmbeddingBase):
    """Offline deterministic embedding used only by the O02 audit fixture."""

    def embed(self, text, memory_action=None):
        dims = int(self.config.embedding_dims or 8)
        vector = [0.0] * dims
        for token in str(text).lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(dims):
                vector[index] += (digest[index] / 255.0) * 2.0 - 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class DeterministicLLM(LLMBase):
    """No-network LLM stub; infer=False means memory CRUD never invokes it."""

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
        **kwargs,
    ):
        return '{"memory": []}'
