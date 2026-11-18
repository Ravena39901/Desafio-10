# Assistente do Regulamento Acadêmico

Sistema de perguntas e respostas sobre o regulamento acadêmico e o manual do aluno (PDFs).
O aluno pergunta, por exemplo, *"quantas faltas posso ter?"*, e o sistema responde **citando o artigo e a página**.
Se a informação não está nos documentos, ele diz que **não encontrou**, em vez de inventar.

- **Backend:** FastAPI (Python) · **Frontend:** React (Vite)
- **IA:** API do Gemini (embeddings + geração) · **Banco vetorial:** ChromaDB (Docker Compose) · **PDF:** pypdf

> **Sobre os PDFs deste repositório.** `backend/data/pdfs/` traz dois PDFs **fictícios** ("Instituição de Ensino Exemplo"),
> gerados por `scripts/gerar_pdfs_exemplo.py`, só para o sistema rodar e os testes passarem.
> Para a demonstração, coloque os PDFs **reais** da instituição nessa pasta e reescreva `backend/eval/perguntas.json`
> (veja [Avaliação](#avaliação-e-taxa-de-acerto)).

## Arquitetura

```
PDF ──pypdf──> páginas ──limpeza──> chunker (artigo/seção + sobreposição) ──> embeddings (Gemini) ──> ChromaDB
                                                                                                        │
Pergunta ──embedding (RETRIEVAL_QUERY)──> busca top-k por cosseno ──> limiar de similaridade ──> Gemini (JSON) ──> validações ──> resposta + fontes
```

| Arquivo (`backend/app/`) | Função |
|---|---|
| `pdf_loader.py` | extrai texto por página; remove cabeçalho, rodapé e números de página; junta palavras hifenizadas |
| `chunker.py` | divide por **artigo** (`Art. N`) ou **seção numerada**; se não houver estrutura, usa janelas com sobreposição |
| `embeddings.py` | `GeminiEmbedder` (`gemini-embedding-001`, 768 dimensões) e um embedder local offline para testes |
| `vectorstore.py` | `ChromaStore` (cosseno) e `MemoriaStore` (testes) |
| `llm.py` | prompt, saída estruturada em JSON (`encontrado`, `resposta`, `fontes`), `GeradorGemini` e gerador extrativo offline |
| `rag.py` | orquestra busca → limiar → geração → validações |
| `avaliacao.py` | métricas: hit@1, hit@k, MRR, taxa de acerto, recusa fora do escopo |
| `main.py` | API: `GET /api/saude`, `GET /api/documentos`, `POST /api/perguntar`, `POST /api/ingestao` |

O núcleo usa interfaces (`Embedder`, `VectorStore`, `Gerador`). Trocar ChromaDB por **pgvector** significa escrever
uma classe `VectorStore` nova, sem mexer no resto.

## Como executar

Pré-requisitos: **Python 3.11+**, **Node 18+**, **Docker Desktop** (Mac ou Windows) e uma chave do Gemini
(<https://aistudio.google.com/apikey>).

### 1. Banco vetorial (ChromaDB)

Na raiz do projeto (Docker Desktop aberto):

```bash
docker compose up -d
```

O Chroma fica em `localhost:8001` e guarda os dados no volume `chroma_data`.

### 2. Backend

**Mac / Linux (Terminal):**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env          # edite e coloque sua GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

**Windows (PowerShell):**
```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1     # se der erro de política: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements-dev.txt
copy .env.example .env         # edite e coloque sua GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Com `AUTO_INGEST=true`, os PDFs de `backend/data/pdfs/` são indexados ao iniciar. Para indexar manualmente:
`python -m scripts.ingerir`. Também é possível enviar PDFs pela interface.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Abra <http://localhost:5173>. O Vite encaminha `/api` para a porta 8000.

### Sem chave do Gemini e sem Docker (modo offline)

Para testar o fluxo sem rede: `PROVIDER=local` (Mac) ou `$env:PROVIDER="local"` (PowerShell). Usa um embedder lexical, banco em memória
e um gerador que apenas devolve o trecho. **Serve para desenvolvimento e testes; a qualidade não representa o Gemini.**

### Variáveis de ambiente (`backend/.env`)

| Variável | Padrão | Descrição |
|---|---|---|
| `PROVIDER` | `gemini` | `gemini` ou `local` |
| `GEMINI_API_KEY` | — | chave da API |
| `EMBEDDING_MODEL` | `gemini-embedding-001` | modelo de embeddings |
| `GENERATION_MODEL` | `gemini-flash-latest` | modelo de geração; liste os disponíveis com `python -m scripts.listar_modelos` |
| `CHROMA_MODE` | `http` | `http` (Docker), `local` (pasta em disco), `memory` |
| `CHROMA_HOST` / `CHROMA_PORT` | `localhost` / `8001` | endereço do Chroma |
| `TAMANHO_TRECHO` / `SOBREPOSICAO` | `1000` / `150` | em caracteres |
| `TOP_K` | `5` | trechos recuperados por pergunta |
| `SCORE_MINIMO` | `0.40` (gemini) / `0.15` (local) | similaridade mínima para chamar o modelo |
| `AUTO_INGEST` | `true` | indexa a pasta de PDFs ao iniciar |

## Testes

```bash
cd backend
python -m pytest -q
```

Cobrem a regra central (a busca devolve o trecho certo e o sistema recusa o que não está no regulamento):
limpeza do PDF, divisão em trechos (artigos, páginas, sobreposição), busca com métricas mínimas
(hit@5 ≥ 80%, hit@1 ≥ 50%, MRR ≥ 0,6), as camadas anti-invenção, a avaliação, o `ChromaStore` e a API.
Os testes usam fakes determinísticos, então **não gastam cota do Gemini**. Os de API e Chroma são pulados
se `fastapi`/`httpx`/`chromadb` não estiverem instalados (com `requirements-dev.txt` eles rodam).

## Avaliação e taxa de acerto

```bash
python -m scripts.avaliar                  # com Gemini: 15 perguntas + fora do escopo
python -m scripts.avaliar --somente-busca  # só mede a recuperação, sem chamar o modelo de geração
python -m scripts.varrer_chunks            # compara tamanhos de trecho e sobreposições
python -m scripts.estimar_custo            # PDF inteiro x só os trechos recuperados
```

`eval/perguntas.json` tem 15 perguntas com **resposta esperada**, **fonte esperada** (arquivo + artigo/seção) e
**palavras-chave** que a resposta precisa conter, além de perguntas fora do escopo. O relatório sai em `eval/resultado.md`.
Uma pergunta conta como **acerto** quando a fonte citada é a esperada **e** a resposta contém a informação esperada.

**Antes da demonstração:** substitua as 15 perguntas pelas do regulamento real, escolhidas pela equipe, e rode com `PROVIDER=gemini`.

## Decisões da equipe

### Por que não enviar o PDF inteiro a cada pergunta?
1. **Custo.** O preço da geração cresce com os tokens de entrada. Enviar o PDF todo multiplica o gasto por pergunta;
   enviando só os 5 trechos mais relevantes a entrada fica bem menor. Em nossos PDFs de exemplo (poucas páginas) a estimativa
   é de ~3.800 tokens contra ~540 (7x menos); com PDFs de dezenas de páginas a diferença aumenta. Rode `scripts.estimar_custo`
   com os PDFs reais para o número da apresentação.
2. **Limite de contexto.** Regulamento + manual podem se aproximar do limite do modelo ou passar dele, e crescem a cada atualização.
3. **Qualidade e citação.** Com menos texto, o modelo tem menos chance de se distrair, e cada trecho já vem com artigo e página,
   o que permite citar com precisão.

### Como escolhemos o tamanho dos trechos e a sobreposição?
- **Unidade natural = artigo.** Normas jurídicas e acadêmicas são escritas em artigos que respondem a uma pergunta inteira
  (parágrafos e incisos ficam junto). Dividir por artigo mantém o sentido e dá citação exata ("Art. 18, p. 3").
  No manual do aluno a unidade é a seção numerada. Sem estrutura reconhecida, o sistema cai para janelas fixas.
- **Tamanho 1000 caracteres (~250 tokens).** É o teto para artigos longos; os curtos ficam inteiros. Trechos pequenos demais perdem contexto
  (o "§ 2º" sem o caput); grandes demais diluem o significado no vetor e gastam tokens.
- **Sobreposição 150 (15%).** Só atua quando um artigo passa do teto: o corte prefere o fim de frase e o trecho seguinte repete o final do anterior, para
  que uma regra que fica na fronteira apareça inteira em algum trecho. A faixa de 10–20% é a prática comum.
- **Não ficamos só no palpite.** `scripts/varrer_chunks.py` testa combinações de tamanho x sobreposição (e compara com janela fixa)
  e mede hit@1, hit@k e MRR. **Resultado com os PDFs de exemplo e o embedder local** (não Gemini): quase todas as
  combinações ficaram entre 80% e 100% de hit@5; a janela fixa ficou no mesmo patamar da divisão por artigo
  (nessa comparação uma janela que cobre dois artigos conta como acerto nos dois, o que favorece as janelas). **Conclusão honesta:** nos
  PDFs de exemplo e com esse embedder, a varredura não separa as configurações. A vantagem comprovada da divisão por artigo
  é a **citação exata de artigo e página**. 1000/150 é nosso ponto de partida; **a equipe deve rodar a varredura com Gemini e os PDFs reais**
  e ajustar `TAMANHO_TRECHO` e `SOBREPOSICAO` se os números pedirem.

### Como medimos se a busca devolve o trecho certo?
Cada pergunta de teste tem a fonte esperada (arquivo + artigo/seção). Medimos:
- **hit@1**: o trecho certo é o primeiro? · **hit@k**: está entre os k recuperados? · **MRR**: média de 1/posição do trecho certo.
- **Taxa de acerto de ponta a ponta**: fonte certa **e** informação esperada na resposta.
- **Recusa fora do escopo**: perguntas sem resposta nos PDFs precisam resultar em "não encontrei".
- **Calibração do limiar**: o relatório mostra o menor score das perguntas válidas e o maior das perguntas fora do escopo, para escolher `SCORE_MINIMO` com dados.

### Como evitamos uma resposta inventada?
Cinco camadas em `rag.py`:
1. **Limiar de similaridade.** Se nenhum trecho passa de `SCORE_MINIMO`, responde "não encontrei" **sem chamar o modelo**.
2. **Contexto restrito + prompt rígido.** O modelo recebe só os trechos recuperados e é instruído a responder apenas com base neles, `temperature = 0`.
3. **Saída estruturada.** O modelo devolve JSON (`encontrado`, `resposta`, `fontes`); se não houver base, deve marcar `encontrado=false`.
4. **Validação das fontes.** Os números de trecho citados precisam existir entre os enviados; resposta "encontrada" sem fonte válida vira "não encontrei".
5. **Verificação das citações.** Todo "Art. N" mencionado na resposta precisa aparecer nos trechos recuperados.

No eval offline, o limiar sozinho recusou a pergunta sobre a Copa do Mundo, mas **deixou passar** a da mensalidade de Medicina
(o embedder local é lexical e achou palavras em comum). Por isso o desenho usa limiar **e** o modelo (camadas 2 e 3), e por isso
a demonstração deve ser feita com o Gemini.

### Por que ChromaDB?
Roda com um contêiner (`docker compose up`), tem cliente Python simples e suporta distância de cosseno. O volume do corpus é pequeno
(centenas de trechos), então pgvector não traria ganho que justifique um PostgreSQL a mais. A interface `VectorStore` permite trocar depois.

## Roteiro da apresentação
1. **Problema e pergunta central** (1 min): PDFs longos; por que não mandar tudo.
2. **Custo** (1 min): rodar `python -m scripts.estimar_custo` com os PDFs reais.
3. **Pipeline** (2 min): diagrama acima; mostrar os trechos (`python -m scripts.ingerir`) e como chunk/overlap foram escolhidos (`varrer_chunks`).
4. **Demonstração** (4 min): `python -m scripts.avaliar` com as 15 perguntas → taxa de acerto; depois, na interface, a pergunta fora do escopo ("não encontrei") e uma pergunta com fonte expandida.
5. **Anti-invenção e limites** (2 min): as 5 camadas e as limitações abaixo.

## Limitações conhecidas
- Os PDFs incluídos são fictícios; **nenhum número de Gemini foi medido neste repositório**. Os números citados acima vêm do modo offline.
- PDFs escaneados (imagem) não têm texto e são rejeitados com mensagem pedindo OCR.
- Tabelas e colunas múltiplas podem sair com a ordem de leitura trocada no pypdf; confira os trechos com `python -m scripts.ingerir`.
- O reconhecimento de artigos assume o formato "Art. N" com numeração crescente; outro formato cai para janelas fixas.
- O nome do modelo de geração (`GENERATION_MODEL`) deve ser conferido com `scripts.listar_modelos`; modelos mudam com o tempo.
- Não há autenticação: é um protótipo.
