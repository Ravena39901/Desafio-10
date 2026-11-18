"""API FastAPI do assistente do regulamento acadêmico.

Rodar:  uvicorn app.main:app --reload --port 8000
Docs interativas: http://localhost:8000/docs
"""
from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import Settings
from .factory import criar_assistente
from .llm import GeracaoErro
from .pdf_loader import PdfSemTextoError
from .rag import TAMANHO_MAXIMO_PERGUNTA, Assistente

log = logging.getLogger("assistente")
TAMANHO_MAXIMO_PDF = 30 * 1024 * 1024  # 30 MB


class PerguntaIn(BaseModel):
    pergunta: str = Field(min_length=3, max_length=TAMANHO_MAXIMO_PERGUNTA, examples=["Quantas faltas posso ter?"])


def _nome_seguro(nome: str) -> str:
    nome = re.sub(r"[^A-Za-z0-9._ -]", "_", Path(nome).name)
    return nome


def criar_app(assistente: Assistente | None = None, settings: Settings | None = None) -> FastAPI:
    """Fábrica da aplicação. Nos testes dá para injetar um `assistente` com componentes falsos."""
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.assistente = assistente or criar_assistente(settings)
        app.state.settings = settings
        if settings.auto_ingest and app.state.assistente.store.total() == 0 and settings.pasta_pdfs.is_dir():
            try:
                resultado = app.state.assistente.ingerir_pasta(settings.pasta_pdfs)
                log.info("Ingestão automática: %s", resultado)
            except Exception:  # noqa: BLE001 - a API deve subir mesmo se a indexação falhar
                log.exception("Falha na ingestão automática dos PDFs")
        yield

    app = FastAPI(title="Assistente do Regulamento Acadêmico", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"]
    )

    @app.get("/api/saude")
    def saude(request: Request):
        a: Assistente = request.app.state.assistente
        return {
            "status": "ok",
            "trechos_indexados": a.store.total(),
            "embedder": a.embedder.nome,
            "gerador": a.gerador.nome,
            "tamanho_trecho": a.tamanho_trecho,
            "sobreposicao": a.sobreposicao,
            "top_k": a.top_k,
            "score_minimo": a.score_minimo,
        }

    @app.get("/api/documentos")
    def documentos(request: Request):
        return {"documentos": request.app.state.assistente.store.documentos()}

    @app.post("/api/perguntar")
    def perguntar(corpo: PerguntaIn, request: Request):
        try:
            resposta = request.app.state.assistente.perguntar(corpo.pergunta)
        except ValueError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
        except GeracaoErro as erro:
            log.error("Erro do modelo: %s", erro)
            raise HTTPException(status_code=502, detail="O modelo de linguagem não respondeu. Tente novamente em instantes.") from erro
        return asdict(resposta)

    @app.post("/api/ingestao")
    def ingestao(request: Request, arquivos: list[UploadFile] = File(...)):
        """Envia um ou mais PDFs e os indexa (substitui a versão anterior do mesmo arquivo)."""
        a: Assistente = request.app.state.assistente
        pasta: Path = request.app.state.settings.pasta_pdfs
        pasta.mkdir(parents=True, exist_ok=True)
        resultado: dict[str, int] = {}
        for arquivo in arquivos:
            nome = _nome_seguro(arquivo.filename or "documento.pdf")
            if not nome.lower().endswith(".pdf"):
                raise HTTPException(status_code=422, detail=f"{nome}: envie apenas arquivos PDF.")
            conteudo = arquivo.file.read(TAMANHO_MAXIMO_PDF + 1)
            if len(conteudo) > TAMANHO_MAXIMO_PDF:
                raise HTTPException(status_code=413, detail=f"{nome}: o PDF passa de 30 MB.")
            destino = pasta / nome
            destino.write_bytes(conteudo)
            try:
                resultado[nome] = a.ingerir_pdf(destino)
            except (PdfSemTextoError, ValueError) as erro:
                destino.unlink(missing_ok=True)
                raise HTTPException(status_code=422, detail=str(erro)) from erro
        return {"indexados": resultado}

    return app


app = criar_app()
