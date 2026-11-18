from __future__ import annotations

import pytest
from pypdf import PdfWriter

from app.models import Pagina
from app.pdf_loader import PdfSemTextoError, ler_pdf, limpar_paginas


def test_extrai_todas_as_paginas_com_acentos(paginas_regulamento):
    assert len(paginas_regulamento) >= 5
    texto = " ".join(p.texto for p in paginas_regulamento)
    assert "Instituição de Ensino Exemplo (IEE)" in texto
    assert "frequência mínima de 75%" in texto
    assert [p.numero for p in paginas_regulamento] == list(range(1, len(paginas_regulamento) + 1))


def test_remove_cabecalho_e_rodape_repetidos(paginas_regulamento):
    for p in paginas_regulamento:
        linhas = p.texto.splitlines()
        assert not any("Regulamento Acadêmico" in l and "—" in l for l in linhas), f"cabeçalho vazou na página {p.numero}"
        assert not any(l.startswith("Página ") for l in linhas), f"rodapé vazou na página {p.numero}"


def test_remove_cabecalho_tambem_em_documento_de_duas_paginas(paginas_manual):
    assert len(paginas_manual) == 2
    assert not any("— Manual do Aluno" in p.texto for p in paginas_manual)


def test_nao_remove_texto_do_corpo():
    corpo = ["Art. {i}. Texto do artigo {i}.", "Primeiro detalhe sobre o tema {i}.", "Segundo detalhe diferente {i}.", "Conclusão específica {i}."]
    paginas = [Pagina(i, "Cabeçalho do documento\n" + "\n".join(l.format(i=i) for l in corpo) + f"\nPágina {i}") for i in (1, 2, 3)]
    limpas = limpar_paginas(paginas)
    for i, pagina in enumerate(limpas, start=1):
        assert pagina.texto.splitlines() == [l.format(i=i) for l in corpo]


def test_pagina_curta_nao_perde_linhas_parecidas_com_cabecalho():
    # páginas de 3 linhas parecidas entre si: nada pode ser tratado como cabeçalho/rodapé
    paginas = [Pagina(i, f"Art. {i}. Texto do artigo {i}.\nParágrafo único {i}.\nVigência {i}.") for i in (1, 2, 3)]
    assert [p.texto for p in limpar_paginas(paginas)] == [p.texto for p in paginas]


def test_junta_palavra_hifenizada_na_quebra_de_linha():
    limpas = limpar_paginas([Pagina(1, "a matrí-\ncula do estudante")])
    assert "matrícula" in limpas[0].texto


def test_pdf_sem_texto_gera_erro_claro(tmp_path):
    escritor = PdfWriter()
    escritor.add_blank_page(width=200, height=200)  # simula um PDF escaneado (sem camada de texto)
    caminho = tmp_path / "escaneado.pdf"
    with open(caminho, "wb") as f:
        escritor.write(f)
    with pytest.raises(PdfSemTextoError, match="OCR"):
        ler_pdf(caminho)
