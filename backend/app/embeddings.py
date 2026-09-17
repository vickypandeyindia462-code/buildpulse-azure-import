"""Provider-swappable embeddings using the shared BuildPulse configuration."""

from __future__ import annotations

import hashlib
import math
import os
from typing import List

from .config import Settings


EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))


def configured_provider() -> str:
    settings = Settings.from_env()
    if settings.llm_provider == "gemini" and settings.gemini_api_key:
        return "gemini"
    if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_embedding_deployment:
        return "azure_openai"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    return "mock"


# Backward compatibility for the verification script and pgvector test.
provider = configured_provider()


def _mock_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """Return a stable local vector without Python's process-randomized hash()."""
    values = [0.0] * dim
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    for index in range(dim):
        values[index] = (digest[index % len(digest)] - 127.5) / 127.5
    magnitude = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / magnitude for value in values]


def get_embedding(text: str) -> List[float]:
    settings = Settings.from_env()
    active_provider = configured_provider()
    if active_provider == "azure_openai":
        from openai import AzureOpenAI

        options = {"azure_endpoint": settings.azure_openai_endpoint, "api_key": settings.azure_openai_api_key}
        if settings.azure_openai_api_version:
            options["api_version"] = settings.azure_openai_api_version
        client = AzureOpenAI(**options)
        response = client.embeddings.create(model=settings.azure_openai_embedding_deployment, input=text)
        return response.data[0].embedding
    if active_provider == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.embeddings.create(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"), input=text
        )
        return response.data[0].embedding
    if active_provider == "gemini":
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.embed_content(
            model=os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001"),
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
        )
        return list(response.embeddings[0].values)
    return _mock_embedding(text)
