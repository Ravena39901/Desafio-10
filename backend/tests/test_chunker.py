from __future__ import annotations

import pytest

from app.chunker import chunk_documento, dividir_com_sobreposicao
from app.models import Pagina

TEXTO_LONGO = " ".join(f"Frase número {i} do regulamento, com algum conteúdo para ocupar espaço." for i in range(1, 41))


# ---------------------------------------------------------------- estrutura por artigo
def test_um_trecho_por_artigo_com_numeracao_completa(paginas_regulamento):
    trechos = chunk_documento("regulamento_exemplo.pdf", paginas_regulamento, 1000, 150)
    referencias = [t.referencia for t in trechos if t.referencia.startswith("Art.")]
    assert referencias == [f"Art. {n}" for n in range(1, 46)]  # 45 artigos, cada um uma vez, em ordem


def test_cada_artigo_aponta_para_a_pagina_onde_comeca(paginas_regulamento, pagina_do_artigo):
    trechos = chunk_documento("regulamento_exemplo.pdf", paginas_regulamento, 1000, 150)
    for t in trechos:
        if t.referencia.startswith("Art."):
            numero = int(t.referencia.split()[1])
            assert t.pagina_inicio == pagina_do_artigo(numero), f"{t.referencia}: página errada"


def test_artigo_guarda_o_capitulo(paginas_regulamento):
    trechos = {t.referencia: t for t in chunk_documento("regulamento_exemplo.pdf", paginas_regulamento)}
    assert trechos["Art. 17"].secao.startswith("CAPÍTULO IV")
    assert "FREQUÊNCIA" in trechos["Art. 17"].secao
    assert "TRANCAMENTO" in trechos["Art. 11"].secao  # título do capítulo quebrado em duas linhas no PDF


def test_artigo_com_incisos_e_paragrafos_fica_inteiro(paginas_regulamento):
    art19 = next(t for t in chunk_documento("regulamento_exemplo.pdf", paginas_regulamento) if t.referencia == "Art. 19")
    assert "regime de exercícios domiciliares" in art19.texto
    assert "§ 2º" in art19.texto and "III –" in art19.texto


def test_ids_sao_unicos_e_estaveis(paginas_regulamento):
    a = chunk_documento("regulamento_exemplo.pdf", paginas_regulamento)
    b = chunk_documento("regulamento_exemplo.pdf", paginas_regulamento)
    assert [t.id for t in a] == [t.id for t in b]
    assert len({t.id for t in a}) == len(a)


def test_referencia_a_artigo_no_meio_da_frase_nao_cria_artigo_novo():
    paginas = [
        Pagina(1, "Art. 1º Primeiro artigo.\nArt. 2º Segundo artigo, nos termos do\nArt. 1º desta norma, vale assim.\nArt. 3º Terceiro artigo.\nArt. 4º Quarto artigo."),
    ]
    referencias = [t.referencia for t in chunk_documento("norma.pdf", paginas)]
    assert referencias == ["Art. 1", "Art. 2", "Art. 3", "Art. 4"]


# ---------------------------------------------------------------- estrutura por seção (manual)
def test_manual_vira_secoes_numeradas(paginas_manual):
    trechos = chunk_documento("manual_aluno_exemplo.pdf", paginas_manual)
    secoes = [t for t in trechos if t.tipo == "secao" and t.referencia.startswith("Seção")]
    assert [t.referencia for t in secoes] == [f"Seção {n}" for n in range(1, 9)]
    assert next(t for t in secoes if t.referencia == "Seção 4").secao == "Biblioteca"


def test_passos_numerados_nao_viram_secoes(paginas_manual):
    # "Passo 1: ..." dentro da Seção 3 não pode abrir uma seção nova
    trechos = chunk_documento("manual_aluno_exemplo.pdf", paginas_manual)
    secao3 = next(t for t in trechos if t.referencia == "Seção 3")
    assert "Passo 1" in secao3.texto and "Passo 5" in secao3.texto


def test_trecho_que_atravessa_paginas_informa_o_intervalo(paginas_manual):
    trechos = chunk_documento("manual_aluno_exemplo.pdf", paginas_manual)
    secao3 = next(t for t in trechos if t.referencia == "Seção 3")
    assert secao3.pagina_inicio == 1 and secao3.pagina_fim == 2
    assert secao3.paginas == "1–2"


# ---------------------------------------------------------------- sem estrutura
def test_sem_estrutura_usa_janelas_numeradas():
    trechos = chunk_documento("livre.pdf", [Pagina(1, TEXTO_LONGO)], tamanho=400, sobreposicao=80)
    assert len(trechos) > 3
    assert all(t.tipo == "janela" for t in trechos)
    assert [t.referencia for t in trechos] == [f"Trecho {i}" for i in range(1, len(trechos) + 1)]


def test_usar_estrutura_false_ignora_artigos(paginas_regulamento):
    trechos = chunk_documento("regulamento_exemplo.pdf", paginas_regulamento, 1000, 150, usar_estrutura=False)
    assert all(t.tipo == "janela" for t in trechos)


# ---------------------------------------------------------------- janelas e sobreposição
def test_janelas_respeitam_o_tamanho_e_cobrem_o_texto_todo():
    janelas = dividir_com_sobreposicao(TEXTO_LONGO, 500, 100)
    assert janelas[0][0] == 0 and janelas[-1][1] == len(TEXTO_LONGO)
    for inicio, fim in janelas:
        assert fim - inicio <= 500
    for (_, fim_a), (inicio_b, _) in zip(janelas, janelas[1:]):
        assert inicio_b <= fim_a, "há uma lacuna entre dois trechos (texto perdido)"


def test_trechos_vizinhos_repetem_a_sobreposicao():
    janelas = dividir_com_sobreposicao(TEXTO_LONGO, 500, 100)
    for (_, fim_a), (inicio_b, _) in zip(janelas, janelas[1:]):
        repetido = fim_a - inicio_b
        assert 40 <= repetido <= 130, f"sobreposição fora do esperado: {repetido}"


def test_sem_sobreposicao_os_trechos_nao_se_repetem():
    janelas = dividir_com_sobreposicao(TEXTO_LONGO, 500, 0)
    for (_, fim_a), (inicio_b, _) in zip(janelas, janelas[1:]):
        assert inicio_b >= fim_a - 1  # no máximo o espaço de separação


def test_corte_prefere_fim_de_frase():
    janelas = dividir_com_sobreposicao(TEXTO_LONGO, 500, 100)
    for _, fim in janelas[:-1]:
        assert TEXTO_LONGO[fim - 1] in ".;:?!\n", f"corte no meio da frase: ...{TEXTO_LONGO[fim - 20:fim]!r}"


def test_artigo_longo_e_dividido_mantendo_a_referencia():
    artigo_longo = "Art. 2º " + TEXTO_LONGO
    paginas = [Pagina(1, f"Art. 1º Primeiro artigo, curto.\n{artigo_longo}\nArt. 3º Terceiro artigo, curto também.\nArt. 4º Último artigo.")]
    trechos = chunk_documento("norma.pdf", paginas, tamanho=400, sobreposicao=80)
    do_art2 = [t for t in trechos if t.referencia == "Art. 2"]
    assert len(do_art2) >= 3
    assert all(len(t.texto) <= 400 for t in do_art2)
    for a, b in zip(do_art2, do_art2[1:]):
        assert b.texto[:30] in a.texto, "o início de um trecho deveria repetir o fim do anterior"
    assert [t.referencia for t in trechos if t.referencia != "Art. 2"] == ["Art. 1", "Art. 3", "Art. 4"]


def test_fragmentos_minusculos_nao_viram_trecho():
    paginas = [Pagina(1, "Art. 1º Texto normal do primeiro artigo.\nArt. 2º Vetado.\nArt. 3º Texto normal do terceiro artigo.\nArt. 4º Texto normal do quarto artigo.")]
    assert [t.referencia for t in chunk_documento("norma.pdf", paginas)] == ["Art. 1", "Art. 3", "Art. 4"]


@pytest.mark.parametrize("tamanho,sobreposicao", [(500, 400), (0, 0), (500, -1)])
def test_sobreposicao_invalida_gera_erro(tamanho, sobreposicao):
    with pytest.raises(ValueError):
        dividir_com_sobreposicao("texto " * 200, tamanho, sobreposicao)
