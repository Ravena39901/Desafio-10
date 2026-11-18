"""Testes da API. Precisam de fastapi e httpx (requirements.txt / requirements-dev.txt); sem eles, são pulados."""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("multipart")

from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import criar_app  # noqa: E402
from app.models import SaidaModelo  # noqa: E402
from app.rag import NAO_ENCONTRADO  # noqa: E402

from .conftest import PASTA_PDFS, REGULAMENTO, GeradorFalso  # noqa: E402


@pytest.fixture
def cliente(criar_assistente, tmp_path):
    gerador = GeradorFalso(SaidaModelo(True, "Até 25% da carga horária (Art. 18, p. 3).", [1]))
    settings = Settings(provider="local", chroma_mode="memory", auto_ingest=False, pasta_pdfs=tmp_path)
    with TestClient(criar_app(criar_assistente(gerador), settings)) as c:
        yield c


def test_saude(cliente):
    dados = cliente.get("/api/saude").json()
    assert dados["status"] == "ok" and dados["trechos_indexados"] > 0
    assert dados["tamanho_trecho"] == 1000 and dados["sobreposicao"] == 150


def test_documentos(cliente):
    nomes = [d["arquivo"] for d in cliente.get("/api/documentos").json()["documentos"]]
    assert nomes == ["manual_aluno_exemplo.pdf", "regulamento_exemplo.pdf"]


def test_perguntar_devolve_resposta_com_fonte(cliente):
    r = cliente.post("/api/perguntar", json={"pergunta": "Quantas faltas posso ter?"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["encontrado"] is True
    assert corpo["fontes"][0]["referencia"] == "Art. 18" and corpo["fontes"][0]["pagina"] >= 1


def test_perguntar_fora_do_escopo_diz_que_nao_encontrou(cliente):
    corpo = cliente.post("/api/perguntar", json={"pergunta": "Quem ganhou a Copa do Mundo de 2022?"}).json()
    assert corpo["encontrado"] is False and corpo["resposta"] == NAO_ENCONTRADO and corpo["fontes"] == []


@pytest.mark.parametrize("corpo", [{"pergunta": "oi"}, {"pergunta": "x" * 501}, {}])
def test_pergunta_invalida_retorna_422(cliente, corpo):
    assert cliente.post("/api/perguntar", json=corpo).status_code == 422


def test_upload_de_pdf_indexa(cliente, tmp_path):
    with open(PASTA_PDFS / REGULAMENTO, "rb") as f:
        r = cliente.post("/api/ingestao", files={"arquivos": ("novo regulamento.pdf", f, "application/pdf")})
    assert r.status_code == 200 and r.json()["indexados"]["novo regulamento.pdf"] > 40
    assert (tmp_path / "novo regulamento.pdf").exists()


def test_upload_rejeita_arquivo_que_nao_e_pdf(cliente):
    r = cliente.post("/api/ingestao", files={"arquivos": ("notas.txt", b"ola", "text/plain")})
    assert r.status_code == 422


def test_upload_rejeita_pdf_sem_texto(cliente, tmp_path):
    from io import BytesIO

    from pypdf import PdfWriter

    escritor, buffer = PdfWriter(), BytesIO()
    escritor.add_blank_page(width=100, height=100)
    escritor.write(buffer)
    r = cliente.post("/api/ingestao", files={"arquivos": ("scan.pdf", buffer.getvalue(), "application/pdf")})
    assert r.status_code == 422 and "OCR" in r.json()["detail"]
    assert not (tmp_path / "scan.pdf").exists()
