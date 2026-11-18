"""Pipeline completo: ingestão dos PDFs e resposta com fontes (RAG).

Camadas contra resposta inventada, na ordem em que acontecem:
  1. Limiar de similaridade: se nenhum trecho passa de `score_minimo`, o modelo nem é chamado.
  2. Contexto restrito: o modelo só recebe os trechos relevantes e é instruído a usar só eles.
  3. Saída estruturada: o modelo diz se encontrou (`encontrado`) e quais trechos usou (`fontes`).
  4. Validação das fontes: números de trecho inexistentes são descartados; sem fonte válida, recusa.
  5. Verificação das citações: artigos citados no texto precisam existir nos trechos enviados.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from .chunker import chunk_documento
from .embeddings import Embedder
from .llm import Gerador
from .models import Achado, Fonte, Resposta
from .pdf_loader import carregar_pdf
from .vectorstore import VectorStore

log = logging.getLogger(__name__)

NAO_ENCONTRADO = (
    "Não encontrei essa informação no regulamento acadêmico nem no manual do aluno. "
    "Procure a Secretaria Acadêmica para confirmar."
)

TAMANHO_MAXIMO_PERGUNTA = 500
_RE_ARTIGO_CITADO = re.compile(r"\bart(?:igo)?s?\.?\s*(\d{1,3})", re.IGNORECASE)


def _numeros_de_artigos(texto: str) -> set[int]:
    return {int(n) for n in _RE_ARTIGO_CITADO.findall(texto)}


class Assistente:
    def __init__(
        self,
        embedder: Embedder,
        store: VectorStore,
        gerador: Gerador,
        *,
        tamanho_trecho: int = 1000,
        sobreposicao: int = 150,
        top_k: int = 5,
        score_minimo: float = 0.40,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.gerador = gerador
        self.tamanho_trecho = tamanho_trecho
        self.sobreposicao = sobreposicao
        self.top_k = top_k
        self.score_minimo = score_minimo

    # ------------------------------------------------------------ ingestão
    def ingerir_pdf(self, caminho: str | Path, nome: str | None = None) -> int:
        """Lê o PDF, divide em trechos, gera os embeddings e grava no banco. Devolve o nº de trechos."""
        caminho = Path(caminho)
        nome = nome or caminho.name
        trechos = chunk_documento(nome, carregar_pdf(caminho), self.tamanho_trecho, self.sobreposicao)
        if not trechos:
            raise ValueError(f"{nome}: nenhum trecho foi gerado a partir do PDF.")
        vetores = self.embedder.embed_documents([t.texto_indexado() for t in trechos])
        self.store.substituir_documento(nome, trechos, vetores)
        log.info("%s: %d trechos indexados", nome, len(trechos))
        return len(trechos)

    def ingerir_pasta(self, pasta: str | Path) -> dict[str, int]:
        resultado: dict[str, int] = {}
        for pdf in sorted(Path(pasta).glob("*.pdf")):
            resultado[pdf.name] = self.ingerir_pdf(pdf)
        return resultado

    # ------------------------------------------------------------ busca
    def buscar(self, pergunta: str, k: int | None = None) -> list[Achado]:
        return self.store.buscar(self.embedder.embed_query(pergunta), k or self.top_k)

    # ------------------------------------------------------------ resposta
    def perguntar(self, pergunta: str) -> Resposta:
        pergunta = " ".join(pergunta.split())
        if len(pergunta) < 3:
            raise ValueError("Escreva uma pergunta com pelo menos 3 caracteres.")
        if len(pergunta) > TAMANHO_MAXIMO_PERGUNTA:
            raise ValueError(f"A pergunta pode ter no máximo {TAMANHO_MAXIMO_PERGUNTA} caracteres.")

        achados = self.buscar(pergunta)
        melhor = achados[0].score if achados else None
        relevantes = [a for a in achados if a.score >= self.score_minimo]

        def recusar(motivo: str) -> Resposta:
            return Resposta(False, NAO_ENCONTRADO, [], motivo, melhor, len(relevantes))

        # camada 1: nada parecido com a pergunta -> não chama o modelo
        if not relevantes:
            return recusar("sem_trechos_relevantes")

        # camadas 2 e 3
        saida = self.gerador.responder(pergunta, relevantes)
        if not saida.encontrado or not saida.resposta:
            return recusar("modelo_nao_encontrou")

        # camada 4: só valem fontes que existem entre os trechos enviados
        indices = list(dict.fromkeys(n for n in saida.fontes if 1 <= n <= len(relevantes)))
        if not indices:
            return recusar("sem_citacao_valida")

        # camada 5: artigos citados no texto precisam existir nos trechos enviados
        permitidos: set[int] = set()
        for a in relevantes:
            permitidos |= _numeros_de_artigos(a.trecho.referencia) | _numeros_de_artigos(a.trecho.texto)
        if _numeros_de_artigos(saida.resposta) - permitidos:
            log.warning("Resposta descartada: cita artigo ausente dos trechos. Resposta: %s", saida.resposta)
            return recusar("citacao_nao_verificada")

        fontes = []
        for n in indices:
            achado = relevantes[n - 1]
            t = achado.trecho
            fontes.append(
                Fonte(
                    arquivo=t.arquivo,
                    referencia=t.referencia,
                    secao=t.secao,
                    pagina=t.pagina_inicio,
                    paginas=t.paginas,
                    trecho=t.texto if len(t.texto) <= 500 else t.texto[:500].rsplit(" ", 1)[0] + "…",
                    score=round(achado.score, 4),
                )
            )
        return Resposta(True, saida.resposta, fontes, "ok", melhor, len(relevantes))
