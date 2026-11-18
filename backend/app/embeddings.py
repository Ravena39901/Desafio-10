"""Geração de embeddings: Gemini (produção) e um embedder lexical local (testes e uso offline)."""
from __future__ import annotations

import hashlib
import math
import re
import time
from collections import Counter
from typing import Callable, Protocol, TypeVar

import numpy as np

from .textutils import normalizar

T = TypeVar("T")


class Embedder(Protocol):
    nome: str

    def embed_documents(self, textos: list[str]) -> list[list[float]]: ...

    def embed_query(self, texto: str) -> list[float]: ...


# ---------------------------------------------------------------- utilidades
def _normalizar_vetor(vetor: list[float]) -> list[float]:
    arr = np.asarray(vetor, dtype=np.float64)
    norma = np.linalg.norm(arr)
    return (arr / norma).tolist() if norma else arr.tolist()


def com_retentativas(funcao: Callable[[], T], tentativas: int = 5, espera_inicial: float = 2.0) -> T:
    """Repete chamadas que falharam por limite de requisições (429) ou instabilidade (503)."""
    espera = espera_inicial
    for tentativa in range(1, tentativas + 1):
        try:
            return funcao()
        except Exception as erro:  # noqa: BLE001 - a SDK levanta vários tipos de erro
            mensagem = str(erro)
            transitorio = any(s in mensagem for s in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "INTERNAL"))
            if not transitorio or tentativa == tentativas:
                raise
            time.sleep(espera)
            espera *= 2
    raise RuntimeError("inalcançável")


# ---------------------------------------------------------------- Gemini
class GeminiEmbedder:
    """Embeddings da API do Gemini. Usa o tipo de tarefa certo para cada lado da busca:
    RETRIEVAL_DOCUMENT para os trechos e RETRIEVAL_QUERY para a pergunta."""

    def __init__(self, api_key: str, modelo: str = "gemini-embedding-001", dimensoes: int = 768, tamanho_lote: int = 50):
        if not api_key:
            raise ValueError("GEMINI_API_KEY não definida. Crie uma chave em https://aistudio.google.com/apikey e coloque no arquivo .env.")
        from google import genai  # importado aqui para o resto do sistema funcionar sem a SDK
        from google.genai import types

        self._types = types
        self._client = genai.Client(api_key=api_key)
        self.modelo = modelo
        self.dimensoes = dimensoes
        self.tamanho_lote = tamanho_lote
        self.nome = f"gemini:{modelo}"

    def _embed(self, textos: list[str], tipo_tarefa: str) -> list[list[float]]:
        vetores: list[list[float]] = []
        for i in range(0, len(textos), self.tamanho_lote):
            lote = textos[i : i + self.tamanho_lote]
            resposta = com_retentativas(
                lambda lote=lote: self._client.models.embed_content(
                    model=self.modelo,
                    contents=lote,
                    config=self._types.EmbedContentConfig(task_type=tipo_tarefa, output_dimensionality=self.dimensoes),
                )
            )
            # com dimensão reduzida o vetor precisa ser normalizado para a similaridade de cosseno ficar correta
            vetores.extend(_normalizar_vetor(list(e.values)) for e in resposta.embeddings)
        return vetores

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        return self._embed(textos, "RETRIEVAL_DOCUMENT")

    def embed_query(self, texto: str) -> list[float]:
        return self._embed([texto], "RETRIEVAL_QUERY")[0]


# ---------------------------------------------------------------- local (offline)
_STOPWORDS = set(
    """a o as os e em um uma uns umas de da do das dos para por com sem sob sobre que se ao aos na no nas nos
    como mais mas ou pelo pela pelos pelas seu sua seus suas ser sao foi ha esta este esse essa isso eu me meu minha
    posso pode podem qual quais quanto quantos quantas quando onde quem faco fazer faz tem ter tenho quero preciso
    deve devem sera serao desde ate entre ja nao sim tambem apos cada outro outra qualquer ser sendo
    aluno alunos estudante estudantes instituicao regulamento manual""".split()
)


def _tokens(texto: str) -> list[str]:
    saida = []
    for tok in re.findall(r"[a-z0-9]+", normalizar(texto)):
        if tok in _STOPWORDS or len(tok) < 2:
            continue
        saida.append(tok if len(tok) <= 5 else tok[:5])  # "trancamento" e "trancar" -> "tranc"
    return saida


class EmbedderLocal:
    """Embedder lexical (saco de palavras com hashing). NÃO entende significado como o Gemini: serve para
    rodar testes e a avaliação sem internet, sem chave de API e sem custo."""

    nome = "local:hashing-lexical"

    def __init__(self, dimensoes: int = 2048):
        self.dimensoes = dimensoes

    def _vetor(self, texto: str) -> list[float]:
        v = np.zeros(self.dimensoes, dtype=np.float64)
        for token, qtd in Counter(_tokens(texto)).items():
            indice = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % self.dimensoes
            v[indice] += 1.0 + math.log(qtd)
        return _normalizar_vetor(v.tolist())

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        return [self._vetor(t) for t in textos]

    def embed_query(self, texto: str) -> list[float]:
        return self._vetor(texto)
