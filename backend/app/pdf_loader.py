"""Leitura dos PDFs com pypdf e limpeza do texto (cabeçalhos, rodapés e números de página)."""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from .models import Pagina
from .textutils import normalizar


class PdfSemTextoError(ValueError):
    """O PDF não tem texto extraível (provavelmente é uma imagem escaneada e precisaria de OCR)."""


# "12", "Página 12", "pág. 12", "12 / 40", "12 de 40"
_RE_NUMERO_PAGINA = re.compile(r"^(?:p[aá]g(?:ina)?\.?\s*)?\d{1,4}(?:\s*(?:/|de)\s*\d{1,4})?$", re.IGNORECASE)


def ler_pdf(caminho: str | Path) -> list[Pagina]:
    """Extrai o texto de cada página, sem limpar nada."""
    leitor = PdfReader(str(caminho))
    if leitor.is_encrypted:
        leitor.decrypt("")  # PDFs protegidos só contra edição abrem com senha vazia
    paginas = [Pagina(numero=i, texto=p.extract_text() or "") for i, p in enumerate(leitor.pages, start=1)]
    if not any(p.texto.strip() for p in paginas):
        raise PdfSemTextoError(f"{Path(caminho).name}: o PDF não tem texto extraível (precisa de OCR).")
    return paginas


def _chave(linha: str) -> str:
    # troca dígitos por "#" para que "Página 3" e "Página 4" contem como a mesma linha repetida
    return re.sub(r"\d+", "#", normalizar(linha))


def limpar_paginas(paginas: list[Pagina]) -> list[Pagina]:
    """Remove linhas que se repetem no topo/rodapé de várias páginas e números de página isolados.
    Também junta palavras hifenizadas na quebra de linha ("matrí-\\ncula" -> "matrícula")."""
    linhas_por_pagina = [[l.strip() for l in p.texto.splitlines() if l.strip()] for p in paginas]

    def borda(n_linhas: int) -> int:
        # até 2 linhas no topo e 2 no rodapé; em páginas curtas a borda encolhe para não apagar texto do corpo
        return min(2, n_linhas // 4)

    repetidas: set[str] = set()
    if len(paginas) >= 2:  # com uma página só não dá para saber o que se repete
        contagem: Counter[str] = Counter()
        for linhas in linhas_por_pagina:
            b = borda(len(linhas))
            contagem.update({_chave(l) for l in linhas[:b] + linhas[len(linhas) - b :]})
        limite = max(2, math.ceil(0.5 * len(paginas)))
        repetidas = {chave for chave, n in contagem.items() if n >= limite}

    limpas: list[Pagina] = []
    for pagina, linhas in zip(paginas, linhas_por_pagina):
        mantidas = []
        b = borda(len(linhas))
        for i, linha in enumerate(linhas):
            na_borda = i < b or i >= len(linhas) - b
            # número de página ("Página 7") pode vir logo após o cabeçalho na extração, então a faixa é maior
            na_faixa_larga = i < 2 or i >= len(linhas) - 2
            if (na_borda and _chave(linha) in repetidas) or (na_faixa_larga and _RE_NUMERO_PAGINA.match(linha)):
                continue
            mantidas.append(linha)
        texto = "\n".join(mantidas)
        texto = re.sub(r"(\w)-\n([a-zà-ú])", r"\1\2", texto)
        limpas.append(Pagina(numero=pagina.numero, texto=texto))
    return limpas


def carregar_pdf(caminho: str | Path) -> list[Pagina]:
    return limpar_paginas(ler_pdf(caminho))
