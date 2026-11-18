"""Banco vetorial: ChromaDB (produção) e uma versão em memória com numpy (testes e modo offline).

Os dois seguem a mesma interface, então trocar por pgvector é escrever outra classe com estes métodos."""
from __future__ import annotations

from typing import Protocol

import numpy as np

from .config import Settings
from .models import Achado, Trecho


class VectorStore(Protocol):
    def substituir_documento(self, arquivo: str, trechos: list[Trecho], vetores: list[list[float]]) -> None: ...

    def buscar(self, vetor: list[float], k: int) -> list[Achado]: ...

    def documentos(self) -> list[dict]: ...

    def total(self) -> int: ...


def _resumir_documentos(trechos: list[Trecho]) -> list[dict]:
    por_arquivo: dict[str, dict] = {}
    for t in trechos:
        d = por_arquivo.setdefault(t.arquivo, {"arquivo": t.arquivo, "trechos": 0, "paginas": 0})
        d["trechos"] += 1
        d["paginas"] = max(d["paginas"], t.pagina_fim)
    return sorted(por_arquivo.values(), key=lambda d: d["arquivo"])


# ---------------------------------------------------------------- em memória
class MemoriaStore:
    def __init__(self) -> None:
        self._trechos: list[Trecho] = []
        self._matriz = np.zeros((0, 0))

    def substituir_documento(self, arquivo: str, trechos: list[Trecho], vetores: list[list[float]]) -> None:
        manter = [(t, v) for t, v in zip(self._trechos, self._matriz) if t.arquivo != arquivo] if self._trechos else []
        novos = list(zip(trechos, np.asarray(vetores, dtype=np.float64)))
        todos = manter + novos
        self._trechos = [t for t, _ in todos]
        self._matriz = np.vstack([v for _, v in todos]) if todos else np.zeros((0, 0))

    def buscar(self, vetor: list[float], k: int) -> list[Achado]:
        if not self._trechos:
            return []
        q = np.asarray(vetor, dtype=np.float64)
        normas = np.linalg.norm(self._matriz, axis=1) * (np.linalg.norm(q) or 1.0)
        normas[normas == 0] = 1.0
        scores = (self._matriz @ q) / normas
        ordem = np.argsort(-scores)[:k]
        return [Achado(trecho=self._trechos[i], score=float(scores[i])) for i in ordem]

    def documentos(self) -> list[dict]:
        return _resumir_documentos(self._trechos)

    def total(self) -> int:
        return len(self._trechos)


# ---------------------------------------------------------------- ChromaDB
class ChromaStore:
    def __init__(self, cliente, nome_colecao: str) -> None:
        # embedding_function=None: nós mesmos geramos os vetores (Gemini); o Chroma só os guarda e busca.
        # hnsw:space=cosine: a distância devolvida é 1 - similaridade de cosseno.
        self._col = cliente.get_or_create_collection(
            name=nome_colecao, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )

    @staticmethod
    def _metadados(t: Trecho) -> dict:
        return {
            "arquivo": t.arquivo,
            "referencia": t.referencia,
            "secao": t.secao,
            "pagina_inicio": t.pagina_inicio,
            "pagina_fim": t.pagina_fim,
            "indice": t.indice,
            "tipo": t.tipo,
        }

    @staticmethod
    def _trecho(id_: str, texto: str, m: dict) -> Trecho:
        return Trecho(
            id=id_, arquivo=m["arquivo"], referencia=m["referencia"], secao=m.get("secao", ""),
            pagina_inicio=int(m["pagina_inicio"]), pagina_fim=int(m["pagina_fim"]),
            texto=texto, indice=int(m["indice"]), tipo=m.get("tipo", "artigo"),
        )

    def substituir_documento(self, arquivo: str, trechos: list[Trecho], vetores: list[list[float]]) -> None:
        self._col.delete(where={"arquivo": arquivo})
        for i in range(0, len(trechos), 200):
            lote = slice(i, i + 200)
            self._col.add(
                ids=[t.id for t in trechos[lote]],
                embeddings=vetores[lote],
                documents=[t.texto for t in trechos[lote]],
                metadatas=[self._metadados(t) for t in trechos[lote]],
            )

    def buscar(self, vetor: list[float], k: int) -> list[Achado]:
        total = self.total()
        if total == 0:
            return []
        r = self._col.query(query_embeddings=[vetor], n_results=min(k, total), include=["documents", "metadatas", "distances"])
        return [
            Achado(trecho=self._trecho(id_, doc, meta), score=1.0 - float(dist))
            for id_, doc, meta, dist in zip(r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0])
        ]

    def documentos(self) -> list[dict]:
        dados = self._col.get(include=["documents", "metadatas"])
        trechos = [self._trecho(i, d, m) for i, d, m in zip(dados["ids"], dados["documents"], dados["metadatas"])]
        return _resumir_documentos(trechos)

    def total(self) -> int:
        return self._col.count()


def criar_chroma(settings: Settings) -> ChromaStore:
    import chromadb

    if settings.chroma_mode == "http":
        cliente = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        try:
            cliente.heartbeat()
        except Exception as erro:  # noqa: BLE001
            raise ConnectionError(
                f"Não consegui falar com o ChromaDB em {settings.chroma_host}:{settings.chroma_port}. "
                "Suba o serviço com `docker compose up -d` (ou use CHROMA_MODE=local no .env)."
            ) from erro
    elif settings.chroma_mode == "local":
        settings.chroma_path.mkdir(parents=True, exist_ok=True)
        cliente = chromadb.PersistentClient(path=str(settings.chroma_path))
    else:
        raise ValueError(f"CHROMA_MODE inválido para o Chroma: {settings.chroma_mode}")
    return ChromaStore(cliente, settings.colecao)
