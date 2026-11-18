"""Configuração lida de variáveis de ambiente (e de um arquivo .env, se existir)."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # pasta backend/


def _carregar_dotenv() -> None:
    """Leitor mínimo de .env (evita depender de python-dotenv).
    Variáveis já definidas no ambiente têm prioridade."""
    for pasta in (BASE_DIR, BASE_DIR.parent):
        arquivo = pasta / ".env"
        if not arquivo.is_file():
            continue
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            chave, valor = linha.split("=", 1)
            valor = valor.strip()
            if valor[:1] in ('"', "'") and valor.count(valor[0]) >= 2:
                valor = valor[1 : valor.index(valor[0], 1)]  # entre aspas: o que vem depois é comentário
            else:
                valor = re.split(r"\s+#", valor, maxsplit=1)[0].strip()  # comentário na mesma linha
            os.environ.setdefault(chave.strip(), valor)


def _bool(valor: str | None, padrao: bool) -> bool:
    if valor is None or valor == "":
        return padrao
    return valor.strip().lower() in {"1", "true", "sim", "yes", "on"}


@dataclass
class Settings:
    # "gemini" usa a API do Google; "local" usa um embedder lexical offline (testes/desenvolvimento).
    provider: str = "gemini"
    gemini_api_key: str = ""
    embedding_model: str = "gemini-embedding-001"
    generation_model: str = "gemini-flash-latest"
    embedding_dims: int = 768

    # "http" = servidor Chroma (Docker Compose); "local" = Chroma embutido em disco; "memory" = em memória (numpy)
    chroma_mode: str = "http"
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_path: Path = BASE_DIR / "data" / "chroma"
    colecao: str = "regulamento"

    # Divisão em trechos e busca
    tamanho_trecho: int = 1000   # caracteres (~250 tokens em português)
    sobreposicao: int = 150      # caracteres (15% do trecho)
    top_k: int = 5
    score_minimo: float = 0.40   # similaridade de cosseno mínima para considerar um trecho relevante

    pasta_pdfs: Path = BASE_DIR / "data" / "pdfs"
    auto_ingest: bool = True
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    @classmethod
    def from_env(cls) -> "Settings":
        _carregar_dotenv()
        e = os.environ.get
        provider = (e("PROVIDER") or "gemini").strip().lower()
        padrao_chroma = "http" if provider == "gemini" else "memory"
        padrao_score = 0.40 if provider == "gemini" else 0.15
        return cls(
            provider=provider,
            gemini_api_key=e("GEMINI_API_KEY", ""),
            embedding_model=e("EMBEDDING_MODEL") or "gemini-embedding-001",
            generation_model=e("GENERATION_MODEL") or "gemini-flash-latest",
            embedding_dims=int(e("EMBEDDING_DIMS") or 768),
            chroma_mode=(e("CHROMA_MODE") or padrao_chroma).strip().lower(),
            chroma_host=e("CHROMA_HOST") or "localhost",
            chroma_port=int(e("CHROMA_PORT") or 8001),
            chroma_path=Path(e("CHROMA_PATH") or BASE_DIR / "data" / "chroma"),
            colecao=e("CHROMA_COLLECTION") or "regulamento",
            tamanho_trecho=int(e("TAMANHO_TRECHO") or 1000),
            sobreposicao=int(e("SOBREPOSICAO") or 150),
            top_k=int(e("TOP_K") or 5),
            score_minimo=float(e("SCORE_MINIMO") or padrao_score),
            pasta_pdfs=Path(e("PASTA_PDFS") or BASE_DIR / "data" / "pdfs"),
            auto_ingest=_bool(e("AUTO_INGEST"), True),
            cors_origins=[o.strip() for o in (e("CORS_ORIGINS") or "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()],
        )
