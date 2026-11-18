"""Compara "mandar o PDF inteiro em cada pergunta" com "mandar só os trechos recuperados".

Mede, com as perguntas de eval/perguntas.json, quantos caracteres (e tokens estimados) cada abordagem envia.
A estimativa usa ~4 caracteres por token, que é uma aproximação para português; para valores exatos use a
contagem de tokens da própria API do Gemini. O custo é proporcional aos tokens de entrada, então informe o
preço atual do modelo com --preco-por-milhao (em R$ ou US$, a mesma moeda sai no resultado).

Uso (dentro da pasta backend):
    python -m scripts.estimar_custo
    python -m scripts.estimar_custo --provider local --perguntas-por-dia 1000 --preco-por-milhao 0.30
"""
from __future__ import annotations

import argparse

from app.avaliacao import carregar_perguntas
from app.config import BASE_DIR, Settings
from app.factory import criar_assistente
from app.llm import INSTRUCAO_SISTEMA, montar_prompt
from app.pdf_loader import carregar_pdf

CARACTERES_POR_TOKEN = 4


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", choices=["gemini", "local"])
    parser.add_argument("--perguntas-por-dia", type=int, default=1000)
    parser.add_argument("--preco-por-milhao", type=float, help="preço por 1 milhão de tokens de ENTRADA")
    args = parser.parse_args()

    s = Settings.from_env()
    if args.provider:
        s.provider = args.provider
        if args.provider == "local":
            s.chroma_mode, s.score_minimo = "memory", 0.15
    a = criar_assistente(s)
    if a.store.total() == 0:
        a.ingerir_pasta(s.pasta_pdfs)

    # PDF inteiro
    paginas = chars_total = 0
    for pdf in sorted(s.pasta_pdfs.glob("*.pdf")):
        ps = carregar_pdf(pdf)
        paginas += len(ps)
        chars_total += sum(len(p.texto) for p in ps)
    tokens_pdf = (chars_total + len(INSTRUCAO_SISTEMA)) // CARACTERES_POR_TOKEN

    # RAG: prompt real que seria enviado em cada pergunta de teste
    dados = carregar_perguntas(BASE_DIR / "eval" / "perguntas.json")
    tamanhos = []
    for item in dados["perguntas"]:
        relevantes = [x for x in a.buscar(item["pergunta"]) if x.score >= a.score_minimo]
        if relevantes:
            tamanhos.append(len(INSTRUCAO_SISTEMA) + len(montar_prompt(item["pergunta"], relevantes)))
    chars_rag = sum(tamanhos) / len(tamanhos)
    tokens_rag = chars_rag / CARACTERES_POR_TOKEN

    print(f"PDFs em {s.pasta_pdfs}: {paginas} páginas, {chars_total:,} caracteres".replace(",", "."))
    print(f"\nTokens de entrada por pergunta (estimativa, ~{CARACTERES_POR_TOKEN} caracteres/token):")
    print(f"  PDF inteiro : {tokens_pdf:>9,.0f}".replace(",", "."))
    print(f"  Só os trechos (top-{a.top_k}, média de {len(tamanhos)} perguntas): {tokens_rag:>9,.0f}".replace(",", "."))
    print(f"  Redução: {tokens_pdf / tokens_rag:.1f}x menos tokens por pergunta")
    por_dia_pdf, por_dia_rag = tokens_pdf * args.perguntas_por_dia, tokens_rag * args.perguntas_por_dia
    print(f"\nCom {args.perguntas_por_dia} perguntas/dia: {por_dia_pdf:,.0f} vs {por_dia_rag:,.0f} tokens de entrada por dia".replace(",", "."))
    if args.preco_por_milhao is not None:
        print(f"Custo de entrada por dia: {por_dia_pdf / 1e6 * args.preco_por_milhao:.2f} vs {por_dia_rag / 1e6 * args.preco_por_milhao:.2f}")
    print("\nO PDF inteiro também precisa caber na janela de contexto do modelo, e a atenção do modelo "
          "tende a piorar quando a resposta está escondida no meio de muito texto.")
    print("Com os PDFs reais (dezenas de páginas) a diferença é bem maior que nos PDFs de exemplo.")


if __name__ == "__main__":
    main()
