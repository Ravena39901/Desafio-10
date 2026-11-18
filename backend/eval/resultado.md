# Resultado da avaliação

- Data: 18/11/2026 03:17
- Embeddings: `local:hashing-lexical` · Gerador: `local:extrativo`
- Trechos: 1000 caracteres, sobreposição 150 · top-k = 5 · limiar = 0.15
- Trechos no banco: 55

## Resumo

| Métrica | Valor |
|---|---|
| **Taxa de acerto** (fonte certa e informação certa) | **10/15 = 66,7%** |
| Busca: trecho certo em 1º lugar (hit@1) | 66,7% |
| Busca: trecho certo entre os 5 primeiros (hit@5) | 93,3% |
| Busca: posição média inversa (MRR) | 0.761 |
| Perguntas fora do escopo recusadas | 1/2 |
| Menor score do melhor trecho nas perguntas do regulamento | 0.0851 |
| Maior score do melhor trecho nas perguntas fora do escopo | 0.1812 |

> Para o limiar (`SCORE_MINIMO`) separar bem os dois grupos, ele deve ficar entre os dois últimos valores.

## Perguntas do regulamento

| # | Pergunta | Resposta esperada | Resposta do sistema | Fontes citadas | Posição na busca | Acertou |
|---|---|---|---|---|---|---|
| 1 | Quantas faltas posso ter? | Até 25% da carga horária da disciplina (frequência mínima de 75%). Exemplo: 15 horas em uma disciplina de 60 horas. | Art. 18. O limite de faltas corresponde a 25% da carga horária de cada disciplina. Assim, em uma disciplina de 60 horas o estudante pode faltar até 15 horas, e em uma disciplina de 80 horas, até 20 horas. (Art. 18, p. 3) | Art. 18 (p. 3) — regulamento_exemplo.pdf | 1 | ✅ |
| 2 | Como faço o trancamento da matrícula? | Pelo Portal do Aluno, em Requerimentos > Trancamento de matrícula, até o trigésimo dia letivo, com justificativa. | Art. 10. O trancamento de matrícula é a suspensão temporária dos estudos, com manutenção do vínculo do estudante com a instituição. (Art. 10, p. 2) | Art. 10 (p. 2) — regulamento_exemplo.pdf | fora do top-k | ❌ |
| 3 | Por quanto tempo posso deixar a matrícula trancada? | No máximo quatro semestres, consecutivos ou não. | Art. 10. O trancamento de matrícula é a suspensão temporária dos estudos, com manutenção do vínculo do estudante com a instituição. (Art. 10, p. 2) | Art. 10 (p. 2) — regulamento_exemplo.pdf | 3 | ❌ |
| 4 | Posso trancar a matrícula no primeiro semestre? | Não, exceto por motivo de saúde comprovado por laudo médico ou convocação para o serviço militar obrigatório. | Art. 14. Não é permitido trancar a matrícula no primeiro semestre do curso, exceto por motivo de saúde comprovado por laudo médico ou por convocação para o serviço militar obrigatório. (Art. 14, p. 2) | Art. 14 (p. 2) — regulamento_exemplo.pdf | 1 | ✅ |
| 5 | Qual a média para ser aprovado sem fazer exame final? | Média parcial igual ou superior a 7,0, com frequência mínima de 75%. | Art. 26. A média final do estudante que fez o exame final é a média aritmética entre a média parcial e a nota do exame final. Será aprovado o estudante cuja média final for igual ou superior a 5,0 (cinco); caso contrário, estará reprovado na disciplina. (Art.… | Art. 26 (p. 4) — regulamento_exemplo.pdf | 4 | ❌ |
| 6 | Quem tem direito de fazer o exame final? | Quem tem média parcial entre 4,0 e 6,9 e frequência mínima de 75%. | Art. 25. O estudante com média parcial entre 4,0 (quatro) e 6,9 (seis vírgula nove) e frequência mínima de 75% terá direito a realizar o exame final. O estudante com média parcial inferior a 4,0 está reprovado, sem direito ao exame final. (Art. 25, p. 4) | Art. 25 (p. 4) — regulamento_exemplo.pdf | 1 | ✅ |
| 7 | Qual média final preciso tirar depois do exame final para passar? | Média final igual ou superior a 5,0 (média aritmética entre a média parcial e a nota do exame). | Art. 26. A média final do estudante que fez o exame final é a média aritmética entre a média parcial e a nota do exame final. Será aprovado o estudante cuja média final for igual ou superior a 5,0 (cinco); caso contrário, estará reprovado na disciplina. (Art.… | Art. 26 (p. 4) — regulamento_exemplo.pdf | 1 | ✅ |
| 8 | Perdi uma prova porque estava doente. O que eu faço? | Pedir segunda chamada pelo Portal do Aluno em até três dias úteis, anexando o atestado médico. | Não encontrei essa informação no regulamento acadêmico nem no manual do aluno. Procure a Secretaria Acadêmica para confirmar. |  | 3 | ❌ |
| 9 | Qual é o prazo para pedir revisão de uma nota? | Até cinco dias úteis após a divulgação da nota, por requerimento ao professor. | Art. 29. O estudante pode solicitar revisão de prova ou de nota em até cinco dias úteis após a divulgação da nota, por requerimento fundamentado dirigido ao professor da disciplina. Persistindo a discordância, o estudante pode recorrer ao Colegiado do Curso e… | Art. 29 (p. 4) — regulamento_exemplo.pdf | 1 | ✅ |
| 10 | O atestado médico abona as faltas? | Não. O atestado serve apenas para pedir a segunda chamada de avaliações perdidas. | Art. 20. O atestado médico não abona faltas. Ele serve apenas como documento comprobatório para solicitar a segunda chamada de avaliações perdidas no período de afastamento, nos termos do Art. 28. (Art. 20, p. 3) | Art. 20 (p. 3) — regulamento_exemplo.pdf | 1 | ✅ |
| 11 | Posso aproveitar uma disciplina que fiz em outra faculdade? | Sim, se houver compatibilidade mínima de 75% de conteúdo e carga horária, com pedido nos primeiros trinta dias do primeiro semestre. | Art. 31. O estudante pode solicitar o aproveitamento (dispensa) de disciplinas cursadas com aprovação em outra instituição de ensino superior reconhecida, desde que haja compatibilidade mínima de 75% entre o conteúdo programático e a carga horária da discipli… | Art. 31 (p. 5) — regulamento_exemplo.pdf | 1 | ✅ |
| 12 | Qual é o prazo máximo para concluir o curso? | Uma vez e meia (1,5) a duração mínima do curso; em um curso de oito semestres, doze semestres. | Art. 40. O prazo máximo para a conclusão do curso é de uma vez e meia (1,5) a duração mínima prevista no projeto pedagógico. Por exemplo, em um curso com duração mínima de oito semestres, o prazo máximo é de doze semestres. Os semestres trancados nos termos d… | Art. 40 (p. 6) — regulamento_exemplo.pdf | 1 | ✅ |
| 13 | Em quanto tempo sai o histórico escolar? | Em até cinco dias úteis após a solicitação pelo Portal do Aluno; a primeira via é gratuita. | Art. 42. O histórico escolar e a declaração de matrícula são emitidos pela Secretaria Acadêmica em até cinco dias úteis após a solicitação feita pelo Portal do Aluno. A primeira via é gratuita. (Art. 42, p. 6) | Art. 42 (p. 6) — regulamento_exemplo.pdf | 1 | ✅ |
| 14 | Quantos livros posso pegar emprestados na biblioteca e por quantos dias? | Até 5 livros ao mesmo tempo, por 7 dias corridos, com até 3 renovações. | 4. Biblioteca A biblioteca funciona de segunda a sexta-feira, das 7h30 às 21h30, e aos sábados, das 8h às 12h. Para pegar livros emprestados, apresente a carteirinha estudantil ou o número da matrícula. Cada estudante pode ter até 5 livros emprestados ao mesm… | Seção 4 (p. 2) — manual_aluno_exemplo.pdf | 1 | ✅ |
| 15 | Como funciona a defesa do TCC e qual nota preciso para ser aprovado? | Defesa pública perante banca de três membros; aprovação com nota final igual ou superior a 7,0. | Art. 32. O resultado da análise do aproveitamento é divulgado em até quinze dias úteis, e as disciplinas dispensadas são registradas no histórico escolar com a observação "aproveitamento de estudos", sem atribuição de nota. (Art. 32, p. 5) | Art. 32 (p. 5) — regulamento_exemplo.pdf | 2 | ❌ |

## Perguntas fora do escopo

| Pergunta | Resposta do sistema | Recusou | Score |
|---|---|---|---|
| Qual é o valor da mensalidade do curso de Medicina? | Art. 14. Não é permitido trancar a matrícula no primeiro semestre do curso, exceto por motivo de saúde comprovado por laudo médico ou por convocação para o ser… | ❌ | 0.1811695595733206 |
| Quem ganhou a Copa do Mundo de 2022? | Não encontrei essa informação no regulamento acadêmico nem no manual do aluno. Procure a Secretaria Acadêmica para confirmar. | ✅ | 0.0 |
