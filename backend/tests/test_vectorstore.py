from __future__ import annotations

import pytest

from app.models import Trecho
from app.vectorstore import MemoriaStore


def _trecho(arquivo: str, i: int, pagina: int = 1) -> Trecho:
    return Trecho(f"{arquivo}:{i}", arquivo, f"Art. {i}", "CAPÍTULO I", pagina, pagina, f"texto {i}", i)


VETORES = {0: [1.0, 0.0, 0.0], 1: [0.0, 1.0, 0.0], 2: [0.7, 0.7, 0.0]}


def _carregar(store, arquivo="a.pdf", indices=(0, 1, 2)):
    store.substituir_documento(arquivo, [_trecho(arquivo, i) for i in indices], [VETORES[i] for i in indices])


def test_busca_devolve_o_mais_parecido_primeiro():
    store = MemoriaStore()
    _carregar(store)
    achados = store.buscar([1.0, 0.1, 0.0], k=3)
    assert [a.trecho.indice for a in achados] == [0, 2, 1]
    assert achados[0].score > 0.99


def test_busca_em_banco_vazio():
    assert MemoriaStore().buscar([1.0, 0.0, 0.0], k=5) == []


def test_k_maior_que_o_total():
    store = MemoriaStore()
    _carregar(store)
    assert len(store.buscar([1.0, 0.0, 0.0], k=50)) == 3


def test_substituir_documento_nao_duplica_nem_apaga_outros():
    store = MemoriaStore()
    _carregar(store, "a.pdf")
    _carregar(store, "b.pdf", indices=(0, 1))
    _carregar(store, "a.pdf", indices=(0,))  # reindexar a.pdf com menos trechos
    assert store.total() == 3
    assert {d["arquivo"]: d["trechos"] for d in store.documentos()} == {"a.pdf": 1, "b.pdf": 2}


def test_documentos_resume_paginas():
    store = MemoriaStore()
    store.substituir_documento("a.pdf", [_trecho("a.pdf", 0, 1), _trecho("a.pdf", 1, 7)], [VETORES[0], VETORES[1]])
    assert store.documentos() == [{"arquivo": "a.pdf", "trechos": 2, "paginas": 7}]


def test_chroma_store_equivale_ao_store_em_memoria():
    """Roda só quando o chromadb está instalado. Usa o cliente efêmero (em memória), sem Docker."""
    chromadb = pytest.importorskip("chromadb")
    from app.vectorstore import ChromaStore

    store = ChromaStore(chromadb.EphemeralClient(), "teste_regulamento")
    _carregar(store)
    achados = store.buscar([1.0, 0.1, 0.0], k=3)
    assert [a.trecho.indice for a in achados] == [0, 2, 1]
    assert achados[0].score > 0.99                      # score = 1 - distância de cosseno
    assert achados[0].trecho.referencia == "Art. 0" and achados[0].trecho.secao == "CAPÍTULO I"
    _carregar(store, indices=(0,))
    assert store.total() == 1
    assert store.documentos()[0]["arquivo"] == "a.pdf"
