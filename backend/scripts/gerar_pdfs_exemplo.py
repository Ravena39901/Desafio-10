"""Gera dois PDFs FICTÍCIOS (regulamento e manual do aluno) para testar o sistema sem os documentos reais.

Uso (dentro da pasta backend):  python -m scripts.gerar_pdfs_exemplo
Requer reportlab (requirements-dev.txt). Para o projeto real, coloque os PDFs verdadeiros em data/pdfs/.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

PASTA = Path(__file__).resolve().parent.parent / "data" / "pdfs"

# ---------------------------------------------------------------- conteúdo do regulamento
# ("cap", "CAPÍTULO I – TÍTULO")  |  ("art", número, [caput, parágrafos/incisos...])
REGULAMENTO = [
    ("cap", "CAPÍTULO I – DISPOSIÇÕES GERAIS"),
    ("art", 1, ["Este Regulamento Acadêmico estabelece as normas de organização didática dos cursos de graduação da Instituição de Ensino Exemplo (IEE), aplicando-se a todos os estudantes regularmente matriculados."]),
    ("art", 2, ["O ano letivo é dividido em dois semestres, cada um com no mínimo cem dias de trabalho acadêmico efetivo, excluído o período reservado aos exames finais."]),
    ("art", 3, ["O Calendário Acadêmico, que define as datas de matrícula, de início e término das aulas, das avaliações e dos exames, será publicado no Portal do Aluno com antecedência mínima de trinta dias do início de cada semestre."]),

    ("cap", "CAPÍTULO II – DO INGRESSO E DA MATRÍCULA"),
    ("art", 4, ["O ingresso nos cursos de graduação ocorre por meio de:",
                "I – processo seletivo (vestibular);", "II – nota do Exame Nacional do Ensino Médio (ENEM);",
                "III – transferência externa ou interna;", "IV – portador de diploma de curso superior, nos termos de edital específico."]),
    ("art", 5, ["A matrícula inicial é realizada no prazo e nas condições definidas em edital, mediante apresentação de documento de identidade, CPF, comprovante de conclusão do ensino médio e uma fotografia 3x4.",
                "Parágrafo único. O candidato que não efetuar a matrícula inicial no prazo perde a vaga, que será oferecida ao próximo classificado."]),
    ("art", 6, ["A renovação da matrícula (rematrícula) é obrigatória a cada semestre letivo e deve ser feita pelo Portal do Aluno nas datas do Calendário Acadêmico. O estudante que não renovar a matrícula e não tiver o trancamento deferido será considerado em situação de abandono de curso."]),
    ("art", 7, ["Em cada semestre, o estudante deve se matricular em no mínimo 12 e no máximo 32 créditos, salvo quando faltar menos que o mínimo para a conclusão do curso. Cada crédito corresponde a 15 horas-aula."]),
    ("art", 8, ["A matrícula em disciplina com pré-requisito depende da aprovação do estudante na disciplina exigida como pré-requisito."]),
    ("art", 9, ["O ajuste de matrícula, que permite incluir ou excluir disciplinas, pode ser solicitado pelo Portal do Aluno até dez dias corridos após o início das aulas, observadas as vagas disponíveis e o limite de créditos do Art. 7º."]),

    ("cap", "CAPÍTULO III – DO TRANCAMENTO E DO CANCELAMENTO DA MATRÍCULA"),
    ("art", 10, ["O trancamento de matrícula é a suspensão temporária dos estudos, com manutenção do vínculo do estudante com a instituição."]),
    ("art", 11, ["O pedido de trancamento deve ser feito pelo estudante no Portal do Aluno, no menu Requerimentos, escolhendo a opção \"Trancamento de matrícula\", até o trigésimo dia letivo do semestre, anexando justificativa por escrito. O pedido é analisado pela Secretaria Acadêmica, que responde em até cinco dias úteis.",
                 "Parágrafo único. Pedidos feitos após o prazo só serão aceitos em caso de motivo de saúde comprovado por laudo médico."]),
    ("art", 12, ["O estudante pode trancar a matrícula por no máximo quatro semestres, consecutivos ou não, ao longo do curso."]),
    ("art", 13, ["Durante o trancamento o estudante não pode cursar disciplinas nem realizar avaliações, e o período trancado não conta para o prazo máximo de conclusão do curso previsto no Art. 40."]),
    ("art", 14, ["Não é permitido trancar a matrícula no primeiro semestre do curso, exceto por motivo de saúde comprovado por laudo médico ou por convocação para o serviço militar obrigatório."]),
    ("art", 15, ["Para retornar após o trancamento, o estudante deve solicitar a reabertura de matrícula pelo Portal do Aluno com antecedência mínima de trinta dias do início do semestre em que pretende retornar."]),
    ("art", 16, ["O cancelamento de matrícula é o desligamento definitivo do curso a pedido do estudante, formalizado por termo de desligamento assinado na Secretaria Acadêmica. O cancelamento é irreversível: para voltar à instituição, o ex-estudante deverá participar novamente de um processo seletivo."]),

    ("cap", "CAPÍTULO IV – DA FREQUÊNCIA"),
    ("art", 17, ["É obrigatória a frequência às aulas e demais atividades acadêmicas de cada disciplina. Será considerado reprovado por falta o estudante que não alcançar a frequência mínima de 75% da carga horária da disciplina, independentemente da nota obtida."]),
    ("art", 18, ["O limite de faltas corresponde a 25% da carga horária de cada disciplina. Assim, em uma disciplina de 60 horas o estudante pode faltar até 15 horas, e em uma disciplina de 80 horas, até 20 horas."]),
    ("art", 19, ["Não existe abono de faltas, exceto nos casos previstos em lei, que garantem regime de exercícios domiciliares:",
                 "I – estudante gestante, a partir do oitavo mês de gestação e durante noventa dias;",
                 "II – estudante com doença infectocontagiosa ou condição de saúde que impeça a presença, comprovada por laudo médico;",
                 "III – estudante convocado para o serviço militar ou para atividades oficiais de representação da instituição.",
                 "§ 1º O pedido de regime de exercícios domiciliares deve ser protocolado na Secretaria Acadêmica, com a documentação comprobatória, em até cinco dias úteis após o início do afastamento.",
                 "§ 2º O regime domiciliar não dispensa a realização das avaliações, que serão aplicadas na forma definida pelo professor da disciplina."]),
    ("art", 20, ["O atestado médico não abona faltas. Ele serve apenas como documento comprobatório para solicitar a segunda chamada de avaliações perdidas no período de afastamento, nos termos do Art. 28."]),
    ("art", 21, ["A frequência é registrada pelo professor no diário de classe, e o estudante pode acompanhar suas faltas pelo Portal do Aluno. Eventuais divergências devem ser comunicadas ao professor em até cinco dias úteis do registro."]),

    ("cap", "CAPÍTULO V – DA AVALIAÇÃO DO RENDIMENTO ESCOLAR"),
    ("art", 22, ["A avaliação do rendimento escolar é contínua e compreende, em cada disciplina, no mínimo duas avaliações por semestre, além dos trabalhos e atividades definidos no plano de ensino."]),
    ("art", 23, ["O rendimento em cada avaliação é expresso em notas de 0 (zero) a 10 (dez), com uma casa decimal."]),
    ("art", 24, ["Será aprovado diretamente na disciplina o estudante que obtiver média parcial igual ou superior a 7,0 (sete) e frequência mínima de 75%."]),
    ("art", 25, ["O estudante com média parcial entre 4,0 (quatro) e 6,9 (seis vírgula nove) e frequência mínima de 75% terá direito a realizar o exame final. O estudante com média parcial inferior a 4,0 está reprovado, sem direito ao exame final."]),
    ("art", 26, ["A média final do estudante que fez o exame final é a média aritmética entre a média parcial e a nota do exame final. Será aprovado o estudante cuja média final for igual ou superior a 5,0 (cinco); caso contrário, estará reprovado na disciplina."]),
    ("art", 27, ["O estudante reprovado deve cursar novamente a disciplina, sujeito a nova frequência e nova avaliação, não havendo aproveitamento de notas de semestres anteriores."]),
    ("art", 28, ["O estudante que não comparecer a uma avaliação poderá requerer segunda chamada pelo Portal do Aluno em até três dias úteis após a data da avaliação perdida, anexando documento que comprove o motivo da ausência (atestado médico, declaração do empregador, intimação judicial ou documento equivalente). A segunda chamada é aplicada em data definida pelo professor, no mesmo semestre."]),
    ("art", 29, ["O estudante pode solicitar revisão de prova ou de nota em até cinco dias úteis após a divulgação da nota, por requerimento fundamentado dirigido ao professor da disciplina. Persistindo a discordância, o estudante pode recorrer ao Colegiado do Curso em até cinco dias úteis da resposta do professor."]),
    ("art", 30, ["Os resultados das avaliações devem ser divulgados no Portal do Aluno em até quinze dias corridos após a sua realização."]),

    ("cap", "CAPÍTULO VI – DO APROVEITAMENTO DE ESTUDOS E DA TRANSFERÊNCIA"),
    ("art", 31, ["O estudante pode solicitar o aproveitamento (dispensa) de disciplinas cursadas com aprovação em outra instituição de ensino superior reconhecida, desde que haja compatibilidade mínima de 75% entre o conteúdo programático e a carga horária da disciplina cursada e os da disciplina da instituição.",
                 "§ 1º O pedido deve ser protocolado na Secretaria Acadêmica nos primeiros trinta dias do primeiro semestre do estudante, anexando o histórico escolar e as ementas autenticadas das disciplinas cursadas.",
                 "§ 2º Podem ser aproveitados no máximo 50% dos créditos do curso.",
                 "§ 3º Disciplinas cursadas há mais de dez anos não serão aproveitadas."]),
    ("art", 32, ["O resultado da análise do aproveitamento é divulgado em até quinze dias úteis, e as disciplinas dispensadas são registradas no histórico escolar com a observação \"aproveitamento de estudos\", sem atribuição de nota."]),
    ("art", 33, ["A transferência externa depende da existência de vagas e é feita por edital, com prova de seleção, exigindo-se que o candidato esteja regularmente matriculado ou com matrícula trancada em curso de graduação reconhecido."]),
    ("art", 34, ["A mudança de curso dentro da instituição (transferência interna) é permitida uma única vez, após a conclusão do primeiro semestre, conforme as vagas e o edital."]),

    ("cap", "CAPÍTULO VII – DO ESTÁGIO E DO TRABALHO DE CONCLUSÃO DE CURSO"),
    ("art", 35, ["O estágio curricular obrigatório deve cumprir a carga horária definida no projeto pedagógico do curso e só pode começar após a assinatura do termo de compromisso de estágio entre o estudante, a empresa e a instituição."]),
    ("art", 36, ["O Trabalho de Conclusão de Curso (TCC) é componente obrigatório e deve ser desenvolvido sob a orientação de um professor da instituição."]),
    ("art", 37, ["O TCC será defendido em sessão pública perante banca examinadora composta por três membros: o orientador, que a preside, e dois outros avaliadores. O texto final deve ser entregue aos membros da banca com antecedência mínima de quinze dias da data da defesa."]),
    ("art", 38, ["Será aprovado no TCC o estudante que obtiver nota final igual ou superior a 7,0 (sete) na média das notas atribuídas pelos membros da banca. O estudante reprovado poderá se matricular novamente no semestre seguinte."]),

    ("cap", "CAPÍTULO VIII – DA CONCLUSÃO DO CURSO E DAS DISPOSIÇÕES FINAIS"),
    ("art", 39, ["A colação de grau ocorre em data prevista no Calendário Acadêmico, após a integralização de todos os componentes curriculares, incluindo estágio, TCC e atividades complementares."]),
    ("art", 40, ["O prazo máximo para a conclusão do curso é de uma vez e meia (1,5) a duração mínima prevista no projeto pedagógico. Por exemplo, em um curso com duração mínima de oito semestres, o prazo máximo é de doze semestres. Os semestres trancados nos termos do Art. 12 não são contados nesse prazo."]),
    ("art", 41, ["Será desligado da instituição o estudante que:",
                 "I – não concluir o curso no prazo máximo do Art. 40;",
                 "II – for reprovado três vezes na mesma disciplina;",
                 "III – permanecer em situação de abandono de curso por dois semestres consecutivos."]),
    ("art", 42, ["O histórico escolar e a declaração de matrícula são emitidos pela Secretaria Acadêmica em até cinco dias úteis após a solicitação feita pelo Portal do Aluno. A primeira via é gratuita."]),
    ("art", 43, ["A instituição poderá aplicar sanções disciplinares (advertência, suspensão e desligamento) ao estudante que praticar fraude em avaliações, plágio ou desrespeito às normas, assegurado o direito de defesa."]),
    ("art", 44, ["Os casos omissos neste Regulamento serão decididos pelo Colegiado do Curso e, em grau de recurso, pelo Conselho Acadêmico."]),
    ("art", 45, ["Este Regulamento entra em vigor na data de sua publicação e revoga as disposições em contrário."]),
]

# ---------------------------------------------------------------- conteúdo do manual
# ("sec", "1. Título")  |  ("p", "parágrafo")
MANUAL = [
    ("sec", "1. Primeiros passos"),
    ("p", "Seja bem-vindo à Instituição de Ensino Exemplo. Este manual reúne as informações práticas do dia a dia: como usar o Portal do Aluno, onde pedir documentos e quais serviços estão à sua disposição. As regras acadêmicas completas estão no Regulamento Acadêmico."),
    ("p", "Guarde o número da sua matrícula. Ele é usado para entrar no Portal do Aluno, na biblioteca e na Secretaria Acadêmica."),

    ("sec", "2. Portal do Aluno"),
    ("p", "O Portal do Aluno é o canal oficial para consultar notas e faltas, renovar a matrícula, pedir documentos e abrir requerimentos. O acesso é feito com o número da matrícula e a senha. Na primeira entrada, a senha são os seis primeiros dígitos do CPF, e o sistema pede a troca imediatamente."),
    ("p", "Quem esquecer a senha deve clicar em \"Esqueci minha senha\" na tela de entrada e seguir as instruções enviadas ao e-mail cadastrado."),

    ("sec", "3. Como solicitar o trancamento de matrícula"),
    ("p", "O trancamento é feito inteiramente pelo Portal do Aluno, sem necessidade de ir à Secretaria. Siga os passos abaixo."),
    ("p", "Passo 1: entre no Portal do Aluno com sua matrícula e senha."),
    ("p", "Passo 2: abra o menu Requerimentos e escolha a opção \"Trancamento de matrícula\"."),
    ("p", "Passo 3: escreva a justificativa e anexe os documentos, se houver (por exemplo, laudo médico)."),
    ("p", "Passo 4: envie o requerimento e anote o número do protocolo."),
    ("p", "Passo 5: acompanhe a resposta na mesma tela. A Secretaria Acadêmica responde em até cinco dias úteis."),
    ("p", "Atenção ao prazo: o pedido precisa ser feito até o trigésimo dia letivo do semestre, conforme o Art. 11 do Regulamento Acadêmico. O trancamento não é permitido no primeiro semestre do curso, salvo motivo de saúde comprovado."),

    ("sec", "4. Biblioteca"),
    ("p", "A biblioteca funciona de segunda a sexta-feira, das 7h30 às 21h30, e aos sábados, das 8h às 12h. Para pegar livros emprestados, apresente a carteirinha estudantil ou o número da matrícula."),
    ("p", "Cada estudante pode ter até 5 livros emprestados ao mesmo tempo, por 7 dias corridos. A renovação pode ser feita até 3 vezes, pelo Portal do Aluno ou no balcão, desde que o livro não tenha sido reservado por outra pessoa. O atraso gera multa de R$ 1,00 por dia e por livro."),

    ("sec", "5. Carteirinha estudantil"),
    ("p", "A primeira via da carteirinha é gratuita e fica pronta em até dez dias úteis após a matrícula. A segunda via, em caso de perda ou dano, custa R$ 15,00 e é emitida em até cinco dias úteis."),

    ("sec", "6. Secretaria Acadêmica"),
    ("p", "O atendimento presencial da Secretaria Acadêmica é de segunda a sexta-feira, das 8h às 20h. Documentos como histórico escolar e declaração de matrícula devem ser pedidos pelo Portal do Aluno, e o prazo de emissão está no Regulamento Acadêmico."),

    ("sec", "7. Auxílios e bolsas"),
    ("p", "O Auxílio Permanência é destinado a estudantes em situação de vulnerabilidade socioeconômica. As inscrições abrem em março e em agosto, pelo Portal do Aluno, e exigem comprovante de renda familiar e comprovante de residência. O resultado é divulgado em até vinte dias corridos após o fim das inscrições."),

    ("sec", "8. Contatos"),
    ("p", "Secretaria Acadêmica: secretaria@exemplo.edu.br. Biblioteca: biblioteca@exemplo.edu.br. Suporte ao Portal do Aluno: suporte@exemplo.edu.br. Os endereços deste documento são fictícios."),
]


# ---------------------------------------------------------------- geração dos PDFs
def _estilos():
    base = getSampleStyleSheet()
    corpo = ParagraphStyle("corpo", parent=base["Normal"], fontName="Helvetica", fontSize=12, leading=19, alignment=TA_JUSTIFY, spaceAfter=11)
    capitulo = ParagraphStyle("cap", parent=corpo, fontName="Helvetica-Bold", fontSize=13, alignment=TA_CENTER, spaceBefore=16, spaceAfter=12)
    titulo = ParagraphStyle("tit", parent=corpo, fontName="Helvetica-Bold", fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=6)
    subtitulo = ParagraphStyle("sub", parent=corpo, alignment=TA_CENTER, spaceAfter=14)
    secao = ParagraphStyle("sec", parent=corpo, fontName="Helvetica-Bold", fontSize=13, spaceBefore=12, spaceAfter=8)
    return corpo, capitulo, titulo, subtitulo, secao


def _documento(caminho: Path, cabecalho: str, elementos: list) -> int:
    def decorar(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.drawString(2.5 * cm, A4[1] - 1.6 * cm, cabecalho)
        canvas.drawRightString(A4[0] - 2.5 * cm, 1.4 * cm, f"Página {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(str(caminho), pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm, topMargin=2.5 * cm, bottomMargin=2.3 * cm, title=caminho.stem)
    doc.build(elementos, onFirstPage=decorar, onLaterPages=decorar)
    return doc.page


def gerar_regulamento(caminho: Path) -> int:
    corpo, capitulo, titulo, subtitulo, _ = _estilos()
    elementos = [
        Paragraph("REGULAMENTO ACADÊMICO DOS CURSOS DE GRADUAÇÃO", titulo),
        Paragraph("Instituição de Ensino Exemplo (IEE)", subtitulo),
        Paragraph("Documento fictício criado apenas para testes do sistema.", subtitulo),
    ]
    for item in REGULAMENTO:
        if item[0] == "cap":
            elementos.append(Paragraph(item[1], capitulo))
            continue
        _, numero, partes = item
        rotulo = f"Art. {numero}º" if numero < 10 else f"Art. {numero}."
        elementos.append(Paragraph(f"<b>{rotulo}</b> {partes[0]}", corpo))
        elementos.extend(Paragraph(p, corpo) for p in partes[1:])
    return _documento(caminho, "Instituição de Ensino Exemplo — Regulamento Acadêmico", elementos)


def gerar_manual(caminho: Path) -> int:
    corpo, _, titulo, subtitulo, secao = _estilos()
    elementos = [
        Paragraph("MANUAL DO ALUNO", titulo),
        Paragraph("Instituição de Ensino Exemplo (IEE)", subtitulo),
        Paragraph("Documento fictício criado apenas para testes do sistema.", subtitulo),
    ]
    for tipo, texto in MANUAL:
        elementos.append(Paragraph(texto, secao if tipo == "sec" else corpo))
    return _documento(caminho, "Instituição de Ensino Exemplo — Manual do Aluno", elementos)


def main() -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    paginas_reg = gerar_regulamento(PASTA / "regulamento_exemplo.pdf")
    paginas_man = gerar_manual(PASTA / "manual_aluno_exemplo.pdf")
    print(f"regulamento_exemplo.pdf: {paginas_reg} páginas")
    print(f"manual_aluno_exemplo.pdf: {paginas_man} páginas")
    print(f"Gerados em {PASTA}")


if __name__ == "__main__":
    main()
