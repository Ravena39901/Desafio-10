"""Divisão do texto em trechos.

Estratégia (decisão da equipe, justificada no README):
1. Respeitar a estrutura do documento. Regulamentos são organizados em artigos ("Art. 17."), então cada
   artigo vira uma unidade. Manuais costumam ter seções numeradas ("3. Biblioteca"), e cada seção vira
   uma unidade. Se não houver estrutura reconhecível, o texto inteiro é dividido em janelas.
2. Só quando uma unidade passa de `tamanho` caracteres ela é cortada em janelas com `sobreposicao`
   caracteres repetidos entre trechos vizinhos (e o corte tenta cair no fim de uma frase).
3. Cada trecho guarda de onde veio: arquivo, artigo/seção, capítulo e páginas.
"""
from __future__ import annotations

import bisect
import re
from dataclasses import dataclass, field

from .models import Pagina, Trecho
from .textutils import slug

# "Art. 17.", "Art. 1º", "Art 5" (somente no início da linha)
RE_ARTIGO = re.compile(r"^Art\.?\s*(\d{1,3})(?!\d)")
# "CAPÍTULO III – DA FREQUÊNCIA", "TÍTULO II", "SEÇÃO I"
RE_CAPITULO = re.compile(r"^(?:CAP[ÍI]TULO|T[ÍI]TULO|SE[ÇC][ÃA]O|SUBSE[ÇC][ÃA]O)\s+[IVXLCDM\d]+\b", re.IGNORECASE)
# "3. Biblioteca" ou "3 Biblioteca" (título curto, sem ponto final)
RE_SECAO_NUM = re.compile(r"^(\d{1,2})\.?\s+([A-ZÀ-Ú][^\n]{2,90})$")
# Marcadores que sempre começam um novo parágrafo
RE_INICIO_PARAGRAFO = re.compile(r"^(?:§|Par[áa]grafo\s+[úu]nico|[IVXLC]{1,6}\s*[-–—)]\s|[a-z]\)\s|Passo\s+\d)")
RE_FIM_FRASE = re.compile(r"[.;:!?]$")

MIN_ARTIGOS_PARA_MODO_ARTIGO = 3
MIN_SECOES_PARA_MODO_SECAO = 2
TAMANHO_MINIMO_TRECHO = 20


@dataclass
class _Unidade:
    referencia: str
    secao: str
    tipo: str
    paragrafos: list[tuple[int, str]] = field(default_factory=list)  # (página, texto)


# ---------------------------------------------------------------- parágrafos
def _eh_cabecalho_capitulo(texto: str) -> bool:
    return bool(RE_CAPITULO.match(texto)) and len(texto) <= 160 and not texto.endswith(".")


def _eh_cabecalho_secao(texto: str) -> bool:
    return bool(RE_SECAO_NUM.match(texto)) and len(texto) <= 100 and not re.search(r"[.;:,]$", texto)


def _inicia_bloco(linha: str) -> bool:
    return bool(RE_ARTIGO.match(linha) or RE_INICIO_PARAGRAFO.match(linha) or _eh_cabecalho_secao(linha) or RE_CAPITULO.match(linha))


def _bloco_fechado(anterior: str, proxima: str) -> bool:
    """O parágrafo anterior terminou? (pontuação final ou cabeçalho completo)"""
    if RE_FIM_FRASE.search(anterior):
        return True
    if _eh_cabecalho_secao(anterior):
        return True
    if RE_CAPITULO.match(anterior):
        # "CAPÍTULO III" pode continuar na linha seguinte em maiúsculas (título quebrado em duas linhas)
        return not proxima.isupper()
    return False


def _juntar_linhas(paginas: list[Pagina]) -> list[tuple[int, str]]:
    """Junta linhas quebradas pelo PDF em parágrafos, guardando a página onde cada parágrafo começa."""
    linhas = [(p.numero, l.strip()) for p in paginas for l in p.texto.splitlines() if l.strip()]
    saida: list[tuple[int, str]] = []
    for pagina, linha in linhas:
        if saida and not _inicia_bloco(linha) and not _bloco_fechado(saida[-1][1], linha):
            saida[-1] = (saida[-1][0], f"{saida[-1][1]} {linha}")
        else:
            saida.append((pagina, linha))
    return saida


# ---------------------------------------------------------------- unidades
def _indices_de_artigos(paragrafos: list[tuple[int, str]]) -> dict[int, int]:
    """Índices dos parágrafos que realmente começam um artigo (e o número do artigo).
    Referências como "... nos termos do\\nArt. 5º" não contam: o parágrafo anterior precisa estar
    encerrado e a numeração precisa crescer."""
    achados: dict[int, int] = {}
    ultimo = 0
    for i, (_, texto) in enumerate(paragrafos):
        m = RE_ARTIGO.match(texto)
        if not m:
            continue
        numero = int(m.group(1))
        anterior = paragrafos[i - 1][1] if i > 0 else ""
        contexto_ok = i == 0 or RE_FIM_FRASE.search(anterior) or _eh_cabecalho_capitulo(anterior) or RE_CAPITULO.match(anterior)
        if contexto_ok and numero > ultimo:
            achados[i] = numero
            ultimo = numero
    return achados


def _indices_de_secoes(paragrafos: list[tuple[int, str]]) -> dict[int, tuple[int, str]]:
    achados: dict[int, tuple[int, str]] = {}
    esperado = 1
    for i, (_, texto) in enumerate(paragrafos):
        m = RE_SECAO_NUM.match(texto)
        if m and _eh_cabecalho_secao(texto) and int(m.group(1)) == esperado:
            achados[i] = (esperado, m.group(2).strip())
            esperado += 1
    return achados


def _dividir_em_unidades(paragrafos: list[tuple[int, str]], usar_estrutura: bool = True) -> list[_Unidade]:
    if not usar_estrutura:
        return [_Unidade("Trecho", "", "janela", list(paragrafos))]

    artigos = _indices_de_artigos(paragrafos)
    if len(artigos) >= MIN_ARTIGOS_PARA_MODO_ARTIGO:
        unidades: list[_Unidade] = []
        capitulo = ""
        atual: _Unidade | None = None
        for i, (pagina, texto) in enumerate(paragrafos):
            if i in artigos:
                atual = _Unidade(f"Art. {artigos[i]}", capitulo, "artigo", [(pagina, texto)])
                unidades.append(atual)
            elif _eh_cabecalho_capitulo(texto):
                capitulo = texto
                atual = None
            else:
                if atual is None:
                    atual = _Unidade("Introdução", capitulo, "artigo")
                    unidades.append(atual)
                atual.paragrafos.append((pagina, texto))
        return unidades

    secoes = _indices_de_secoes(paragrafos)
    if len(secoes) >= MIN_SECOES_PARA_MODO_SECAO:
        unidades = []
        atual = None
        for i, (pagina, texto) in enumerate(paragrafos):
            if i in secoes:
                numero, titulo = secoes[i]
                atual = _Unidade(f"Seção {numero}", titulo, "secao", [(pagina, texto)])
                unidades.append(atual)
            else:
                if atual is None:
                    atual = _Unidade("Introdução", "", "secao")
                    unidades.append(atual)
                atual.paragrafos.append((pagina, texto))
        return unidades

    return [_Unidade("Trecho", "", "janela", list(paragrafos))]


# ---------------------------------------------------------------- janelas com sobreposição
def dividir_com_sobreposicao(texto: str, tamanho: int, sobreposicao: int) -> list[tuple[int, int]]:
    """Devolve (início, fim) de cada janela. Cada janela tem no máximo `tamanho` caracteres e repete
    cerca de `sobreposicao` caracteres da janela anterior. O fim tenta coincidir com o fim de uma frase."""
    if tamanho <= 0 or not 0 <= sobreposicao <= tamanho // 2:
        raise ValueError("A sobreposição deve ficar entre 0 e metade do tamanho do trecho.")
    n = len(texto)
    if n <= tamanho:
        return [(0, n)]

    janelas: list[tuple[int, int]] = []
    inicio = 0
    while True:
        fim = min(inicio + tamanho, n)
        if fim < n:
            limite_inferior = inicio + int(tamanho * 0.7)
            cortes = [texto.rfind(sep, limite_inferior, fim) for sep in ("\n", ". ", "; ", ": ", "? ", "! ")]
            corte = max(cortes)
            if corte != -1:
                fim = corte + 1  # inclui a pontuação/quebra
        janelas.append((inicio, fim))
        if fim >= n:
            break
        proximo = fim - sobreposicao
        if proximo > 0 and not texto[proximo - 1].isspace():
            achou = re.search(r"\s", texto[proximo:fim])  # não começar no meio de uma palavra
            if achou:
                proximo += achou.end()
        inicio = max(proximo, inicio + 1)
    return janelas


# ---------------------------------------------------------------- função principal
def chunk_documento(
    arquivo: str,
    paginas: list[Pagina],
    tamanho: int = 1000,
    sobreposicao: int = 150,
    usar_estrutura: bool = True,
) -> list[Trecho]:
    """`usar_estrutura=False` ignora artigos/seções e corta o texto em janelas fixas (serve de comparação)."""
    paragrafos = _juntar_linhas(paginas)
    trechos: list[Trecho] = []
    base_id = slug(arquivo)

    for unidade in _dividir_em_unidades(paragrafos, usar_estrutura):
        texto = ""
        inicios: list[int] = []  # deslocamento de cada parágrafo dentro de `texto`
        paginas_dos_paragrafos: list[int] = []
        for pagina, paragrafo in unidade.paragrafos:
            if texto:
                texto += "\n"
            inicios.append(len(texto))
            paginas_dos_paragrafos.append(pagina)
            texto += paragrafo

        def pagina_em(deslocamento: int) -> int:
            posicao = bisect.bisect_right(inicios, max(deslocamento, 0)) - 1
            return paginas_dos_paragrafos[max(posicao, 0)]

        for inicio, fim in dividir_com_sobreposicao(texto, tamanho, sobreposicao):
            pedaco = texto[inicio:fim]
            esquerda = len(pedaco) - len(pedaco.lstrip())
            pedaco = pedaco.strip()
            if len(pedaco) < TAMANHO_MINIMO_TRECHO:
                continue
            indice = len(trechos)
            referencia = unidade.referencia if unidade.tipo != "janela" else f"Trecho {indice + 1}"
            trechos.append(
                Trecho(
                    id=f"{base_id}:{indice:04d}",
                    arquivo=arquivo,
                    referencia=referencia,
                    secao=unidade.secao,
                    pagina_inicio=pagina_em(inicio + esquerda),
                    pagina_fim=pagina_em(fim - 1),
                    texto=pedaco,
                    indice=indice,
                    tipo=unidade.tipo,
                )
            )
    return trechos
