"""A busca devolve o trecho certo? Mede hit@k e MRR com as 15 perguntas de eval/perguntas.json.

Aqui o embedder é o lexical local (determinístico, sem internet): o teste protege o pipeline de PDF, divisão
em trechos e busca contra regressões. A qualidade com o Gemini é medida por `python -m scripts.avaliar`."""
from __future__ import annotations

from app.avaliacao import avaliar


def test_quinze_perguntas_de_teste(dados_avaliacao):
    assert len(dados_avaliacao["perguntas"]) == 15
    for p in dados_avaliacao["perguntas"]:
        assert p["fontes_esperadas"] and p["resposta_esperada"] and p["palavras_chave"]
    assert len(dados_avaliacao["fora_do_escopo"]) >= 1


def test_busca_acha_o_trecho_certo_na_maioria_das_perguntas(criar_assistente, dados_avaliacao):
    resumo = avaliar(criar_assistente(top_k=5), dados_avaliacao, usar_modelo=False)["resumo"]
    assert resumo["hit_at_k"] >= 0.8, resumo
    assert resumo["hit_at_1"] >= 0.5, resumo
    assert resumo["mrr"] >= 0.6, resumo


def test_aumentar_o_top_k_nao_piora_a_busca(criar_assistente, dados_avaliacao):
    k3 = avaliar(criar_assistente(top_k=3), dados_avaliacao, usar_modelo=False)["resumo"]["hit_at_k"]
    k8 = avaliar(criar_assistente(top_k=8), dados_avaliacao, usar_modelo=False)["resumo"]["hit_at_k"]
    assert k8 >= k3


def test_pergunta_de_outro_assunto_fica_abaixo_do_limiar(criar_assistente):
    achados = criar_assistente().buscar("Quem ganhou a Copa do Mundo de 2022?")
    assert not achados or achados[0].score < 0.15


def test_busca_devolve_resultados_ordenados_por_score(criar_assistente):
    scores = [a.score for a in criar_assistente().buscar("trancamento da matrícula", k=8)]
    assert scores == sorted(scores, reverse=True)
    assert len(scores) == 8


def test_busca_nos_dois_documentos(criar_assistente):
    arquivos = {a.trecho.arquivo for a in criar_assistente().buscar("biblioteca empréstimo de livros renovação", k=5)}
    assert "manual_aluno_exemplo.pdf" in arquivos
