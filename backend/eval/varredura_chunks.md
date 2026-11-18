# Varredura de tamanho de trecho e sobreposição

Embeddings: `local:hashing-lexical` · top-k = 5 · 15 perguntas

| Divisão | Tamanho | Sobreposição | Nº de trechos | hit@1 | hit@k | MRR |
|---|---|---|---|---|---|---|
| por artigo/seção | 300 | 0 | 68 | 73% | 100% | 0.819 |
| por artigo/seção | 300 | 100 | 72 | 67% | 100% | 0.789 |
| por artigo/seção | 300 | 150 | 77 | 67% | 100% | 0.789 |
| por artigo/seção | 500 | 0 | 58 | 67% | 100% | 0.774 |
| por artigo/seção | 500 | 100 | 58 | 67% | 100% | 0.778 |
| por artigo/seção | 500 | 150 | 58 | 67% | 100% | 0.778 |
| por artigo/seção | 500 | 250 | 60 | 67% | 100% | 0.778 |
| por artigo/seção | 800 | 0 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 800 | 100 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 800 | 150 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 800 | 250 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1000 | 0 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1000 | 100 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1000 | 150 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1000 | 250 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1500 | 0 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1500 | 100 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1500 | 150 | 55 | 67% | 93% | 0.761 |
| por artigo/seção | 1500 | 250 | 55 | 67% | 93% | 0.761 |
| janela fixa | 300 | 0 | 54 | 60% | 93% | 0.744 |
| janela fixa | 300 | 100 | 82 | 60% | 80% | 0.689 |
| janela fixa | 300 | 150 | 113 | 73% | 87% | 0.780 |
| janela fixa | 500 | 0 | 32 | 67% | 93% | 0.772 |
| janela fixa | 500 | 100 | 42 | 67% | 93% | 0.772 |
| janela fixa | 500 | 150 | 48 | 73% | 87% | 0.800 |
| janela fixa | 500 | 250 | 69 | 73% | 87% | 0.789 |
| janela fixa | 800 | 0 | 21 | 87% | 100% | 0.933 |
| janela fixa | 800 | 100 | 23 | 73% | 100% | 0.817 |
| janela fixa | 800 | 150 | 25 | 67% | 100% | 0.782 |
| janela fixa | 800 | 250 | 29 | 67% | 100% | 0.797 |
| janela fixa | 1000 | 0 | 16 | 73% | 93% | 0.811 |
| janela fixa | 1000 | 100 | 17 | 67% | 100% | 0.789 |
| janela fixa | 1000 | 150 | 19 | 73% | 100% | 0.839 |
| janela fixa | 1000 | 250 | 21 | 87% | 100% | 0.933 |
| janela fixa | 1500 | 0 | 11 | 73% | 93% | 0.822 |
| janela fixa | 1500 | 100 | 12 | 73% | 100% | 0.847 |
| janela fixa | 1500 | 150 | 12 | 80% | 100% | 0.889 |
| janela fixa | 1500 | 250 | 13 | 93% | 100% | 0.956 |
