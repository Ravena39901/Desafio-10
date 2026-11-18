from __future__ import annotations

import pytest

from app.avaliacao import alguma_fonte_confere, fonte_confere, palavras_presentes, posicao_da_fonte, taxa
from app.models import Achado, Fonte, Trecho


def _achado(arquivo: str, referencia: str, score: float = 0.5) -> Achado:
    return Achado(Trecho("id", arquivo, referencia, "", 1, 1, "texto do trecho", 0), score)


ESPERADAS = [{"arquivo": "reg.pdf", "referencia": "Art. 17"}, {"arquivo": "reg.pdf", "referencia": "Art. 18"}]


def test_fonte_confere_ignora_caixa_e_acentos():
    assert fonte_confere("reg.pdf", "art. 17", ESPERADAS)
    assert not fonte_confere("reg.pdf", "Art. 19", ESPERADAS)
    assert not fonte_confere("outro.pdf", "Art. 17", ESPERADAS)


def test_posicao_da_fonte_e_a_primeira_correta():
    achados = [_achado("reg.pdf", "Art. 5"), _achado("reg.pdf", "Art. 18"), _achado("reg.pdf", "Art. 17")]
    assert posicao_da_fonte(achados, ESPERADAS) == 2
    assert posicao_da_fonte(achados[:1], ESPERADAS) is None


def test_palavras_chave_em_grupos_com_alternativas():
    grupos = [["75%", "setenta e cinco"], ["falta", "frequência"]]
    assert palavras_presentes("A frequência mínima é de 75%.", grupos)
    assert palavras_presentes("SETENTA E CINCO por cento de FREQUÊNCIA", grupos)
    assert not palavras_presentes("A frequência mínima é alta.", grupos)  # falta o grupo do número
    assert palavras_presentes("qualquer coisa", [])


def test_alguma_fonte_confere():
    fontes = [Fonte("reg.pdf", "Art. 3", "", 1, "1", "t", 0.5), Fonte("reg.pdf", "Art. 17", "", 3, "3", "t", 0.6)]
    assert alguma_fonte_confere(fontes, ESPERADAS)
    assert not alguma_fonte_confere(fontes[:1], ESPERADAS)


def test_taxa():
    assert taxa([True, False, True, True]) == 0.75
    assert taxa([]) == 0.0


@pytest.mark.parametrize("posicoes,mrr", [([1, 1], 1.0), ([1, 2], 0.75), ([None, 4], 0.125)])
def test_mrr_do_resumo(criar_assistente, posicoes, mrr):
    # calcula o MRR com a mesma fórmula usada em avaliar(): média de 1/posição, ausente conta zero
    assert sum(1 / p for p in posicoes if p) / len(posicoes) == pytest.approx(mrr)
