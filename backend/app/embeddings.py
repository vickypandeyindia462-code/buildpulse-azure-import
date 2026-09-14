import os
from typing import List

# load .env if present for local development
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

# Minimal embedding wrapper supporting Azure (azure-ai-inference) or OpenAI fallback.
# If no provider configured, returns a deterministic mock embedding (hash-based) for local dev.

EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

# support multiple env var name patterns used elsewhere: AZURE_AI_*, AZURE_*
AZURE_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT") or os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_AI_API_KEY") or os.getenv("AZURE_API_KEY") or os.getenv("AZURE_KEY")

client = None
provider = None
if AZURE_ENDPOINT and AZURE_API_KEY:
    try:
        # Prefer azure.ai.openai if available; many Azure SDK variants exist.
        from azure.ai.openai import OpenAI as AzureOpenAI

        client = AzureOpenAI(endpoint=AZURE_ENDPOINT, credential=AZURE_API_KEY)
        provider = "azure"
    except Exception:
        try:
            from azure.ai import OpenAI

            client = OpenAI(endpoint=AZURE_ENDPOINT, credential=AZURE_API_KEY)
            provider = "azure"
        except Exception:
            client = None
            provider = None

try:
    import openai

    if provider is None and (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")):
        openai.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
        provider = "openai"
except Exception:
    pass


def _mock_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    # deterministic pseudo-embedding based on character codes
    h = [0.0] * dim
    for i, ch in enumerate(text.encode("utf-8")):
        h[i % dim] += (ch % 97) / 97.0
    # normalize
    s = sum(x * x for x in h) ** 0.5 or 1.0
    return [x / s for x in h]


def get_embedding(text: str) -> List[float]:
    """Return embedding vector for given text as list of floats.

    Tries Azure -> OpenAI -> mock fallback.
    """
    if client is not None and provider == "azure":
        try:
            # azure.ai.OpenAI client usage: client.embeddings.create(model=..., input=text)
            model = os.getenv("AZURE_EMBEDDING_MODEL", "text-embedding-3-small")
            resp = client.embeddings.create(model=model, input=text)
            return resp.data[0].embedding
        except Exception:
            pass

    if "openai" in globals() and os.getenv("OPENAI_API_KEY"):
        try:
            model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            r = openai.Embeddings.create(model=model, input=text)
            return r["data"][0]["embedding"]
        except Exception:
            pass

    # fallback
    return _mock_embedding(text, EMBEDDING_DIM)
