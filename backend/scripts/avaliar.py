"""Roda as perguntas de teste (eval/perguntas.json) e calcula as métricas da demonstração.

Uso (dentro da pasta backend):
    python -m scripts.avaliar                    # busca + resposta (usa o Gemini)
    python -m scripts.avaliar --somente-busca    # só mede se a busca acha o trecho certo (sem gerar respostas)
    python -m scripts.avaliar --provider local   # offline, só para checar o funcionamento (NÃO representa o Gemini)

Gera eval/resultado.md e eval/resultado.json.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from app.avaliacao import avaliar, carregar_perguntas
from app.config import BASE_DIR, Settings
from app.factory import criar_assistente


def _pct(x: float | None) -> str:
    return "—" if x is None else f"{x * 100:.1f}%".replace(".", ",")


def _celula(texto: str, limite: int = 160) -> str:
    texto = " ".join(str(texto).split()).replace("|", "\\|")
    return texto if len(texto) <= limite else texto[: limite - 1] + "…"


def gerar_markdown(a, resultado: dict, usar_modelo: bool, perguntas_ok: int) -> str:
    r = resultado["resumo"]
    linhas = [
        "# Resultado da avaliação",
        "",
        f"- Data: {datetime.now():%d/%m/%Y %H:%M}",
        f"- Embeddings: `{a.embedder.nome}` · Gerador: `{a.gerador.nome if usar_modelo else '(não usado)'}`",
        f"- Trechos: {a.tamanho_trecho} caracteres, sobreposição {a.sobreposicao} · top-k = {a.top_k} · limiar = {a.score_minimo}",
        f"- Trechos no banco: {a.store.total()}",
        "",
        "## Resumo",
        "",
        "| Métrica | Valor |",
        "|---|---|",
    ]
    if usar_modelo:
        linhas.append(f"| **Taxa de acerto** (fonte certa e informação certa) | **{perguntas_ok}/{r['perguntas']} = {_pct(r['taxa_de_acerto'])}** |")
    linhas += [
        f"| Busca: trecho certo em 1º lugar (hit@1) | {_pct(r['hit_at_1'])} |",
        f"| Busca: trecho certo entre os {r['top_k']} primeiros (hit@{r['top_k']}) | {_pct(r['hit_at_k'])} |",
        f"| Busca: posição média inversa (MRR) | {r['mrr']:.3f} |",
        f"| Perguntas fora do escopo recusadas | {r['fora_do_escopo_recusadas']} |",
        f"| Menor score do melhor trecho nas perguntas do regulamento | {r['menor_score_com_resposta']} |",
        f"| Maior score do melhor trecho nas perguntas fora do escopo | {r['maior_score_fora_do_escopo']} |",
        "",
        "> Para o limiar (`SCORE_MINIMO`) separar bem os dois grupos, ele deve ficar entre os dois últimos valores.",
        "",
        "## Perguntas do regulamento",
        "",
    ]
    if usar_modelo:
        linhas += ["| # | Pergunta | Resposta esperada | Resposta do sistema | Fontes citadas | Posição na busca | Acertou |", "|---|---|---|---|---|---|---|"]
        for x in resultado["resultados"]:
            linhas.append(
                f"| {x.id} | {_celula(x.pergunta)} | {_celula(x.resposta_esperada)} | {_celula(x.resposta, 260)} | "
                f"{_celula('; '.join(x.fontes))} | {x.posicao or 'fora do top-k'} | {'✅' if x.acertou else '❌'} |"
            )
    else:
        linhas += ["| # | Pergunta | Resposta esperada | Posição do trecho certo | Score |", "|---|---|---|---|---|"]
        for x in resultado["resultados"]:
            linhas.append(f"| {x.id} | {_celula(x.pergunta)} | {_celula(x.resposta_esperada)} | {x.posicao or 'fora do top-k'} | {x.melhor_score} |")

    linhas += ["", "## Perguntas fora do escopo", "", "| Pergunta | Resposta do sistema | Recusou | Score |", "|---|---|---|---|"]
    for f in resultado["fora_do_escopo"]:
        linhas.append(f"| {_celula(f.pergunta)} | {_celula(f.resposta) or '(não gerada)'} | {'✅' if f.recusou else '❌'} | {f.melhor_score} |")
    return "\n".join(linhas) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--perguntas", type=Path, default=BASE_DIR / "eval" / "perguntas.json")
    parser.add_argument("--saida", type=Path, default=BASE_DIR / "eval" / "resultado", help="prefixo dos arquivos de saída")
    parser.add_argument("--somente-busca", action="store_true")
    parser.add_argument("--provider", choices=["gemini", "local"], help="substitui PROVIDER do .env")
    args = parser.parse_args()

    settings = Settings.from_env()
    if args.provider and args.provider != settings.provider:
        settings.provider = args.provider
        settings.chroma_mode = "memory" if args.provider == "local" else settings.chroma_mode
        settings.score_minimo = 0.15 if args.provider == "local" else settings.score_minimo

    assistente = criar_assistente(settings)
    if assistente.store.total() == 0:
        print("Banco vazio: indexando os PDFs de", settings.pasta_pdfs)
        assistente.ingerir_pasta(settings.pasta_pdfs)

    usar_modelo = not args.somente_busca
    resultado = avaliar(assistente, carregar_perguntas(args.perguntas), usar_modelo)
    acertos = sum(bool(x.acertou) for x in resultado["resultados"])

    markdown = gerar_markdown(assistente, resultado, usar_modelo, acertos)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.with_suffix(".md").write_text(markdown, encoding="utf-8")
    args.saida.with_suffix(".json").write_text(
        json.dumps(
            {"resumo": resultado["resumo"], "resultados": [asdict(x) for x in resultado["resultados"]], "fora_do_escopo": [asdict(x) for x in resultado["fora_do_escopo"]]},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(markdown)
    print(f"Salvo em {args.saida.with_suffix('.md')} e {args.saida.with_suffix('.json')}")


if __name__ == "__main__":
    main()
