from __future__ import annotations

from pathlib import Path

import pytest

from app.avaliacao import carregar_perguntas
from app.embeddings import EmbedderLocal
from app.llm import GeradorExtrativo
from app.models import Achado, SaidaModelo
from app.pdf_loader import carregar_pdf
from app.rag import Assistente
from app.vectorstore import MemoriaStore

RAIZ = Path(__file__).resolve().parent.parent
PASTA_PDFS = RAIZ / "data" / "pdfs"
REGULAMENTO = "regulamento_exemplo.pdf"
MANUAL = "manual_aluno_exemplo.pdf"
LIMIAR_LOCAL = 0.15  # limiar adequado ao embedder lexical local (o do Gemini é outro)


class GeradorFalso:
    """Gerador controlável: devolve o que o teste mandar e registra as chamadas."""

    nome = "falso"

    def __init__(self, saida: SaidaModelo | None = None):
        self.saida = saida or SaidaModelo(True, "resposta", [1])
        self.chamadas: list[tuple[str, list[Achado]]] = []

    def responder(self, pergunta: str, achados: list[Achado]) -> SaidaModelo:
        self.chamadas.append((pergunta, achados))
        return self.saida


@pytest.fixture(scope="session")
def paginas_regulamento():
    return carregar_pdf(PASTA_PDFS / REGULAMENTO)


@pytest.fixture(scope="session")
def paginas_manual():
    return carregar_pdf(PASTA_PDFS / MANUAL)


@pytest.fixture(scope="session")
def indice():
    """Embedder + banco em memória já com os dois PDFs de exemplo indexados (criado uma vez)."""
    embedder, store = EmbedderLocal(), MemoriaStore()
    Assistente(embedder, store, GeradorExtrativo(), score_minimo=LIMIAR_LOCAL).ingerir_pasta(PASTA_PDFS)
    return embedder, store


@pytest.fixture
def criar_assistente(indice):
    embedder, store = indice

    def _criar(gerador=None, **kwargs):
        kwargs.setdefault("score_minimo", LIMIAR_LOCAL)
        return Assistente(embedder, store, gerador or GeradorExtrativo(), **kwargs)

    return _criar


@pytest.fixture(scope="session")
def dados_avaliacao():
    return carregar_perguntas(RAIZ / "eval" / "perguntas.json")


@pytest.fixture(scope="session")
def pagina_do_artigo(paginas_regulamento):
    """Descobre em qual página do PDF cada artigo começa (referência independente do chunker)."""

    def _pagina(numero: int) -> int:
        marcador = f"Art. {numero}º" if numero < 10 else f"Art. {numero}."
        for p in paginas_regulamento:
            if any(linha.startswith(marcador) for linha in p.texto.splitlines()):
                return p.numero
        raise AssertionError(f"Art. {numero} não encontrado no PDF")

    return _pagina
