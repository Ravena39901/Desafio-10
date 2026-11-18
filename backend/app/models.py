"""Estruturas de dados compartilhadas pelo sistema."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePath


@dataclass
class Pagina:
    numero: int  # começa em 1
    texto: str


@dataclass
class Trecho:
    """Pedaço do documento que vira um vetor no banco."""

    id: str
    arquivo: str
    referencia: str      # "Art. 17", "Seção 3" ou "Introdução"
    secao: str           # capítulo (regulamento) ou título da seção (manual); pode ser vazio
    pagina_inicio: int
    pagina_fim: int
    texto: str
    indice: int
    tipo: str = "artigo"  # "artigo" | "secao" | "janela"

    @property
    def titulo_documento(self) -> str:
        return PurePath(self.arquivo).stem.replace("_", " ").replace("-", " ")

    @property
    def paginas(self) -> str:
        if self.pagina_inicio == self.pagina_fim:
            return str(self.pagina_inicio)
        return f"{self.pagina_inicio}–{self.pagina_fim}"

    def texto_indexado(self) -> str:
        """Texto que gera o embedding: o trecho com um cabeçalho de contexto.
        O cabeçalho ajuda a busca a saber de qual documento, artigo e capítulo o trecho vem."""
        cabecalho = f"Documento: {self.titulo_documento}\n{self.referencia}"
        if self.secao:
            cabecalho += f" — {self.secao}"
        return f"{cabecalho}\n{self.texto}"


@dataclass
class Achado:
    """Resultado da busca vetorial: um trecho e sua similaridade (cosseno, 0 a 1) com a pergunta."""

    trecho: Trecho
    score: float


@dataclass
class Fonte:
    arquivo: str
    referencia: str
    secao: str
    pagina: int
    paginas: str
    trecho: str
    score: float


@dataclass
class Resposta:
    encontrado: bool
    resposta: str
    fontes: list[Fonte] = field(default_factory=list)
    # ok | sem_trechos_relevantes | modelo_nao_encontrou | sem_citacao_valida | citacao_nao_verificada
    motivo: str = "ok"
    melhor_score: float | None = None
    trechos_consultados: int = 0


@dataclass
class SaidaModelo:
    """O que o modelo de linguagem devolve (JSON estruturado)."""

    encontrado: bool
    resposta: str
    fontes: list[int]  # números dos trechos usados (1 = primeiro trecho enviado)
