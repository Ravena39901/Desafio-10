"""Monta o Assistente de acordo com as configurações (.env)."""
from __future__ import annotations

from .config import Settings
from .embeddings import EmbedderLocal, GeminiEmbedder
from .llm import GeradorExtrativo, GeradorGemini
from .rag import Assistente
from .vectorstore import MemoriaStore, criar_chroma


def criar_assistente(settings: Settings | None = None) -> Assistente:
    settings = settings or Settings.from_env()

    if settings.provider == "gemini":
        embedder = GeminiEmbedder(settings.gemini_api_key, settings.embedding_model, settings.embedding_dims)
        gerador = GeradorGemini(settings.gemini_api_key, settings.generation_model)
    elif settings.provider == "local":
        embedder, gerador = EmbedderLocal(), GeradorExtrativo()
    else:
        raise ValueError(f"PROVIDER inválido: {settings.provider!r} (use 'gemini' ou 'local').")

    store = MemoriaStore() if settings.chroma_mode == "memory" else criar_chroma(settings)

    return Assistente(
        embedder,
        store,
        gerador,
        tamanho_trecho=settings.tamanho_trecho,
        sobreposicao=settings.sobreposicao,
        top_k=settings.top_k,
        score_minimo=settings.score_minimo,
    )
