"""Compara tamanhos de trecho e sobreposições para escolher os valores com dados, não por palpite.

Para cada combinação, indexa os PDFs numa memória temporária e mede a busca (hit@1, hit@k, MRR) com as
perguntas de eval/perguntas.json. Também compara "dividir por artigo/seção" com "janela fixa".
Os vetores de trechos idênticos são reaproveitados, então o número de chamadas à API é pequeno.

Uso (dentro da pasta backend):
    python -m scripts.varrer_chunks
    python -m scripts.varrer_chunks --provider local     # offline (não representa o Gemini)
    python -m scripts.varrer_chunks --tamanhos 400 800 1200 --sobreposicoes 0 100 200
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.avaliacao import avaliar, carregar_perguntas
from app.chunker import chunk_documento
from app.config import BASE_DIR, Settings
from app.embeddings import EmbedderLocal, GeminiEmbedder
from app.llm import GeradorExtrativo
from app.pdf_loader import carregar_pdf
from app.rag import Assistente
from app.vectorstore import MemoriaStore


class EmbedderComCache:
    def __init__(self, interno):
        self.interno, self.nome, self._cache = interno, interno.nome, {}

    def embed_documents(self, textos):
        faltam = [t for t in dict.fromkeys(textos) if t not in self._cache]
        if faltam:
            self._cache.update(zip(faltam, self.interno.embed_documents(faltam)))
        return [self._cache[t] for t in textos]

    def embed_query(self, texto):
        return self.interno.embed_query(texto)


def _plano(texto: str) -> str:
    return " ".join(texto.split())


def rotular_janelas(janelas, unidades, minimo=100):
    """Janelas fixas se chamam "Trecho N" e nunca bateriam com "Art. 18". Para comparar de forma justa,
    cada janela recebe como rótulo todos os artigos/seções dos quais contém pelo menos `minimo` caracteres
    seguidos (ou o texto inteiro, se a unidade for menor que isso)."""
    for j in janelas:
        corpo = _plano(j.texto)
        rotulos = []
        for u in unidades:
            alvo = _plano(u.texto)
            sonda = min(minimo, len(alvo))
            if any(alvo[i : i + sonda] in corpo for i in range(0, len(alvo) - sonda + 1, 20)):
                rotulos.append(u.referencia)
        if rotulos:
            j.referencia = " | ".join(rotulos)


def medir(embedder, paginas_por_pdf, dados, tamanho, sobreposicao, estrutura, top_k, limiar):
    store = MemoriaStore()
    total = 0
    for nome, paginas in paginas_por_pdf.items():
        trechos = chunk_documento(nome, paginas, tamanho, sobreposicao, usar_estrutura=estrutura)
        if not estrutura:
            unidades = chunk_documento(nome, paginas, 100_000, 0, usar_estrutura=True)
            rotular_janelas(trechos, unidades)
        store.substituir_documento(nome, trechos, embedder.embed_documents([t.texto_indexado() for t in trechos]))
        total += len(trechos)
    a = Assistente(embedder, store, GeradorExtrativo(), tamanho_trecho=tamanho, sobreposicao=sobreposicao, top_k=top_k, score_minimo=limiar)
    r = avaliar(a, dados, usar_modelo=False)["resumo"]
    return total, r


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tamanhos", type=int, nargs="+", default=[300, 500, 800, 1000, 1500])
    parser.add_argument("--sobreposicoes", type=int, nargs="+", default=[0, 100, 150, 250])
    parser.add_argument("--provider", choices=["gemini", "local"])
    parser.add_argument("--pasta", type=Path)
    parser.add_argument("--saida", type=Path, default=BASE_DIR / "eval" / "varredura_chunks.md")
    args = parser.parse_args()

    s = Settings.from_env()
    provider = args.provider or s.provider
    base = EmbedderLocal() if provider == "local" else GeminiEmbedder(s.gemini_api_key, s.embedding_model, s.embedding_dims)
    embedder = EmbedderComCache(base)
    limiar = 0.15 if provider == "local" else s.score_minimo
    dados = carregar_perguntas(BASE_DIR / "eval" / "perguntas.json")
    pasta = args.pasta or s.pasta_pdfs
    paginas_por_pdf = {p.name: carregar_pdf(p) for p in sorted(pasta.glob("*.pdf"))}

    linhas = [
        "# Varredura de tamanho de trecho e sobreposição", "",
        f"Embeddings: `{embedder.nome}` · top-k = {s.top_k} · {len(dados['perguntas'])} perguntas", "",
        "| Divisão | Tamanho | Sobreposição | Nº de trechos | hit@1 | hit@k | MRR |", "|---|---|---|---|---|---|---|",
    ]
    for estrutura in (True, False):
        for tamanho in args.tamanhos:
            for sobre in args.sobreposicoes:
                if sobre > tamanho // 2:
                    continue
                total, r = medir(embedder, paginas_por_pdf, dados, tamanho, sobre, estrutura, s.top_k, limiar)
                linha = f"| {'por artigo/seção' if estrutura else 'janela fixa'} | {tamanho} | {sobre} | {total} | {r['hit_at_1']:.0%} | {r['hit_at_k']:.0%} | {r['mrr']:.3f} |"
                linhas.append(linha)
                print(linha)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"\nSalvo em {args.saida}")


if __name__ == "__main__":
    main()
