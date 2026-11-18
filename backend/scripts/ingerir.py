"""Indexa os PDFs da pasta data/pdfs no banco vetorial.

Uso (dentro da pasta backend):
    python -m scripts.ingerir                 # usa a pasta e as configurações do .env
    python -m scripts.ingerir --pasta outra/  # outra pasta de PDFs
Reexecutar substitui os trechos dos mesmos arquivos (não duplica).
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.config import Settings
from app.factory import criar_assistente


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pasta", type=Path, help="pasta com os PDFs (padrão: PASTA_PDFS do .env)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    settings = Settings.from_env()
    pasta = args.pasta or settings.pasta_pdfs
    assistente = criar_assistente(settings)

    print(f"Embeddings: {assistente.embedder.nome} | trecho={assistente.tamanho_trecho} sobreposição={assistente.sobreposicao}")
    resultado = assistente.ingerir_pasta(pasta)
    if not resultado:
        print(f"Nenhum PDF encontrado em {pasta}")
        return
    for nome, n in resultado.items():
        print(f"  {nome}: {n} trechos")
    print(f"Total no banco: {assistente.store.total()} trechos")


if __name__ == "__main__":
    main()
