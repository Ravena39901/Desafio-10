"""Testes da regra central: responder citando artigo e página, e recusar quando não há base no regulamento."""
from __future__ import annotations

import pytest

from app.llm import GeracaoErro, interpretar_saida, montar_prompt
from app.models import SaidaModelo
from app.rag import NAO_ENCONTRADO, TAMANHO_MAXIMO_PERGUNTA

from .conftest import GeradorFalso

PERGUNTA_FALTAS = "Quantas faltas posso ter?"
PERGUNTA_FORA = "Quem ganhou a Copa do Mundo de 2022?"


# ---------------------------------------------------------------- recusa sem chamar o modelo
def test_assunto_fora_do_regulamento_recusa_sem_chamar_o_modelo(criar_assistente):
    gerador = GeradorFalso()
    resposta = criar_assistente(gerador).perguntar(PERGUNTA_FORA)

    assert resposta.encontrado is False
    assert resposta.resposta == NAO_ENCONTRADO
    assert resposta.fontes == []
    assert resposta.motivo == "sem_trechos_relevantes"
    assert gerador.chamadas == [], "o modelo não deveria ser chamado quando nada na busca é relevante"


def test_limiar_alto_recusa_ate_pergunta_valida(criar_assistente):
    gerador = GeradorFalso()
    resposta = criar_assistente(gerador, score_minimo=0.99).perguntar(PERGUNTA_FALTAS)
    assert resposta.encontrado is False and gerador.chamadas == []


# ---------------------------------------------------------------- resposta com fonte
def test_resposta_cita_artigo_e_pagina(criar_assistente, pagina_do_artigo):
    gerador = GeradorFalso(SaidaModelo(True, "Até 25% da carga horária (Art. 18, p. 3).", [1]))
    resposta = criar_assistente(gerador).perguntar(PERGUNTA_FALTAS)

    assert resposta.encontrado is True and resposta.motivo == "ok"
    fonte = resposta.fontes[0]
    assert fonte.arquivo == "regulamento_exemplo.pdf"
    assert fonte.referencia == "Art. 18"
    assert fonte.pagina == pagina_do_artigo(18)
    assert "25%" in fonte.trecho
    assert fonte.score > 0


def test_modelo_recebe_so_trechos_relevantes_numerados_com_origem(criar_assistente):
    gerador = GeradorFalso()
    criar_assistente(gerador).perguntar(PERGUNTA_FALTAS)
    pergunta, achados = gerador.chamadas[0]
    prompt = montar_prompt(pergunta, achados)

    assert pergunta == PERGUNTA_FALTAS
    assert all(a.score >= 0.15 for a in achados)
    assert "[1] regulamento_exemplo.pdf · Art. 18 · p. 3" in prompt
    assert prompt.rstrip().endswith(f"PERGUNTA: {PERGUNTA_FALTAS}")


# ---------------------------------------------------------------- camadas contra invenção
def test_modelo_diz_que_nao_encontrou(criar_assistente):
    gerador = GeradorFalso(SaidaModelo(False, "", []))
    resposta = criar_assistente(gerador).perguntar(PERGUNTA_FALTAS)
    assert (resposta.encontrado, resposta.motivo, resposta.resposta) == (False, "modelo_nao_encontrou", NAO_ENCONTRADO)


def test_resposta_sem_fonte_valida_e_recusada(criar_assistente):
    gerador = GeradorFalso(SaidaModelo(True, "Pode faltar quanto quiser.", [99, 0, -1]))
    resposta = criar_assistente(gerador).perguntar(PERGUNTA_FALTAS)
    assert (resposta.encontrado, resposta.motivo) == (False, "sem_citacao_valida")


def test_fontes_inexistentes_sao_descartadas_e_as_validas_ficam(criar_assistente):
    gerador = GeradorFalso(SaidaModelo(True, "Até 25% (Art. 18).", [1, 99, 1]))
    resposta = criar_assistente(gerador).perguntar(PERGUNTA_FALTAS)
    assert resposta.encontrado is True
    assert len(resposta.fontes) == 1  # 99 descartado e o "1" repetido contado uma vez


def test_artigo_inventado_no_texto_e_bloqueado(criar_assistente):
    gerador = GeradorFalso(SaidaModelo(True, "Pode faltar até 50% das aulas (Art. 99).", [1]))
    resposta = criar_assistente(gerador).perguntar(PERGUNTA_FALTAS)
    assert (resposta.encontrado, resposta.motivo) == (False, "citacao_nao_verificada")


def test_referencia_cruzada_dentro_do_trecho_e_aceita(criar_assistente):
    """O Art. 20 diz "nos termos do Art. 28": citar o 28 junto com o 20 é legítimo."""
    assistente = criar_assistente(GeradorFalso(SaidaModelo(True, "O atestado não abona faltas (Art. 20); veja a segunda chamada no Art. 28.", [1])))
    achados = assistente.buscar("O atestado médico abona as faltas?")
    assert "Art. 20" in [a.trecho.referencia for a in achados if a.score >= 0.15]
    assert assistente.perguntar("O atestado médico abona as faltas?").encontrado is True


# ---------------------------------------------------------------- validação de entrada
@pytest.mark.parametrize("pergunta", ["", "  ", "oi"])
def test_pergunta_muito_curta_gera_erro(criar_assistente, pergunta):
    with pytest.raises(ValueError):
        criar_assistente().perguntar(pergunta)


def test_pergunta_muito_longa_gera_erro(criar_assistente):
    with pytest.raises(ValueError):
        criar_assistente().perguntar("faltas " * TAMANHO_MAXIMO_PERGUNTA)


# ---------------------------------------------------------------- ingestão
def test_reindexar_substitui_em_vez_de_duplicar(criar_assistente, indice):
    _, store = indice
    assistente = criar_assistente()
    antes = store.total()
    assistente.ingerir_pasta(assistente_pasta())
    assert store.total() == antes


def assistente_pasta():
    from .conftest import PASTA_PDFS

    return PASTA_PDFS


# ---------------------------------------------------------------- saída do modelo
def test_interpretar_saida_aceita_json_com_cerca_de_codigo():
    saida = interpretar_saida('```json\n{"encontrado": true, "resposta": "ok (Art. 1)", "fontes": [1, 2]}\n```')
    assert saida == SaidaModelo(True, "ok (Art. 1)", [1, 2])


@pytest.mark.parametrize("texto", ["", "isto não é json", '{"resposta": "sem campo encontrado"}', '{"encontrado": true, "fontes": ["a"]}'])
def test_interpretar_saida_rejeita_formato_invalido(texto):
    with pytest.raises(GeracaoErro):
        interpretar_saida(texto)
