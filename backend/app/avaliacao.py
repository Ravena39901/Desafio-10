"""Métricas da demonstração: a busca devolve o trecho certo? A resposta está certa? E fora do escopo, recusa?

Formato de cada pergunta em eval/perguntas.json:
  {"id": 1, "pergunta": "...", "resposta_esperada": "texto para os slides",
   "fontes_esperadas": [{"arquivo": "regulamento_exemplo.pdf", "referencia": "Art. 17"}],
   "palavras_chave": [["75%", "25%"], ["falta", "frequência"]]}
`palavras_chave` é uma lista de grupos: cada grupo precisa ter pelo menos uma alternativa na resposta.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .models import Achado, Fonte, Resposta
from .textutils import normalizar


# ---------------------------------------------------------------- funções puras (testadas)
def fonte_confere(arquivo: str, referencia: str, esperadas: list[dict]) -> bool:
    # a referência pode ter várias partes separadas por " | " (usado na comparação com janelas fixas)
    obtidas = {normalizar(r) for r in referencia.split(" | ")}
    return any(e["arquivo"] == arquivo and normalizar(e["referencia"]) in obtidas for e in esperadas)


def posicao_da_fonte(achados: list[Achado], esperadas: list[dict]) -> int | None:
    """Posição (1 = primeiro) do primeiro trecho esperado na lista devolvida pela busca; None se ausente."""
    for posicao, a in enumerate(achados, start=1):
        if fonte_confere(a.trecho.arquivo, a.trecho.referencia, esperadas):
            return posicao
    return None


def palavras_presentes(resposta: str, grupos: list[list[str]]) -> bool:
    texto = normalizar(resposta)
    return all(any(normalizar(alt) in texto for alt in grupo) for grupo in grupos)


def alguma_fonte_confere(fontes: list[Fonte], esperadas: list[dict]) -> bool:
    return any(fonte_confere(f.arquivo, f.referencia, esperadas) for f in fontes)


def taxa(valores: list[bool]) -> float:
    return sum(valores) / len(valores) if valores else 0.0


def carregar_perguntas(caminho: str | Path) -> dict:
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- execução
@dataclass
class ResultadoPergunta:
    id: int
    pergunta: str
    resposta_esperada: str
    posicao: int | None            # posição do trecho certo na busca
    melhor_score: float | None
    resposta: str = ""
    fontes: list[str] = field(default_factory=list)
    fonte_ok: bool | None = None
    palavras_ok: bool | None = None
    acertou: bool | None = None    # só preenchido quando o modelo de linguagem é usado
    motivo: str = ""


@dataclass
class ResultadoForaEscopo:
    pergunta: str
    recusou: bool
    melhor_score: float | None
    motivo: str
    resposta: str


def avaliar(assistente, dados: dict, usar_modelo: bool = True) -> dict:
    """Roda todas as perguntas. `usar_modelo=False` mede só a busca (não gasta chamadas de geração)."""
    k = assistente.top_k
    resultados: list[ResultadoPergunta] = []

    for item in dados["perguntas"]:
        achados = assistente.buscar(item["pergunta"], k)
        r = ResultadoPergunta(
            id=item["id"],
            pergunta=item["pergunta"],
            resposta_esperada=item["resposta_esperada"],
            posicao=posicao_da_fonte(achados, item["fontes_esperadas"]),
            melhor_score=round(achados[0].score, 4) if achados else None,
        )
        if usar_modelo:
            resp: Resposta = assistente.perguntar(item["pergunta"])
            r.resposta = resp.resposta
            r.motivo = resp.motivo
            r.fontes = [f"{f.referencia} (p. {f.paginas}) — {f.arquivo}" for f in resp.fontes]
            r.fonte_ok = resp.encontrado and alguma_fonte_confere(resp.fontes, item["fontes_esperadas"])
            r.palavras_ok = resp.encontrado and palavras_presentes(resp.resposta, item.get("palavras_chave", []))
            r.acertou = bool(r.fonte_ok and r.palavras_ok)
        resultados.append(r)

    fora: list[ResultadoForaEscopo] = []
    for item in dados.get("fora_do_escopo", []):
        achados = assistente.buscar(item["pergunta"], k)
        if usar_modelo:
            resp = assistente.perguntar(item["pergunta"])
            fora.append(ResultadoForaEscopo(item["pergunta"], not resp.encontrado, resp.melhor_score, resp.motivo, resp.resposta))
        else:
            melhor = achados[0].score if achados else None
            fora.append(ResultadoForaEscopo(item["pergunta"], melhor is None or melhor < assistente.score_minimo, melhor, "", ""))

    posicoes = [r.posicao for r in resultados]
    resumo = {
        "perguntas": len(resultados),
        "top_k": k,
        "hit_at_1": taxa([p == 1 for p in posicoes]),
        "hit_at_k": taxa([p is not None for p in posicoes]),
        "mrr": sum(1 / p for p in posicoes if p) / len(posicoes) if posicoes else 0.0,
        "taxa_de_acerto": taxa([bool(r.acertou) for r in resultados]) if usar_modelo else None,
        "fora_do_escopo_recusadas": f"{sum(f.recusou for f in fora)}/{len(fora)}",
        # ajudam a escolher o limiar (SCORE_MINIMO): o menor score do melhor trecho nas perguntas
        # do regulamento deve ficar ACIMA do maior score nas perguntas fora do escopo
        "menor_score_com_resposta": min((r.melhor_score for r in resultados if r.melhor_score is not None), default=None),
        "maior_score_fora_do_escopo": (
            round(max(f.melhor_score for f in fora if f.melhor_score is not None), 4)
            if any(f.melhor_score is not None for f in fora) else None
        ),
        "limiar_atual": assistente.score_minimo,
    }
    return {"resumo": resumo, "resultados": resultados, "fora_do_escopo": fora}
