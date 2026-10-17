"""Deterministic offline providers used only by the O02 Mem0 smoke fixture."""

from __future__ import annotations

import hashlib
import json
import math

from mem0.embeddings.base import EmbeddingBase
from mem0.llms.base import LLMBase


def deterministic_embedding(text: str, dimensions: int = 8) -> list[float]:
    """Map text to a stable, normalized vector without models or network I/O."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [((digest[index] / 255.0) * 2.0) - 1.0 for index in range(dimensions)]
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


class DeterministicEmbedder(EmbeddingBase):
    def __init__(self, config):
        super().__init__(config)
        self.dimensions = config.embedding_dims or 8

    def embed(self, text, memory_action=None):
        return deterministic_embedding(str(text), self.dimensions)


class DeterministicLLM(LLMBase):
    """Offline LLM guard: raw-memory fixture should never invoke inference."""

    def generate_response(self, messages, response_format=None, tools=None, tool_choice="auto"):
        raise AssertionError(
            "DeterministicLLM was called; the offline fixture must use infer=False"
        )
