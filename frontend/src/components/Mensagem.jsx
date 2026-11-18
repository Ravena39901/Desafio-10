import Fonte from "./Fonte.jsx";

export default function Mensagem({ mensagem }) {
  if (mensagem.papel === "aluno") {
    return <div className="msg aluno">{mensagem.texto}</div>;
  }
  if (mensagem.erro) {
    return <div className="msg erro" role="alert">{mensagem.erro}</div>;
  }
  const r = mensagem.resposta;
  return (
    <div className={`msg assistente ${r.encontrado ? "" : "nao-encontrado"}`}>
      {!r.encontrado && <div className="selo">Não encontrei</div>}
      <p>{r.resposta}</p>
      {r.fontes.length > 0 && (
        <>
          <h4>Fontes</h4>
          <ul className="fontes">
            {r.fontes.map((f, i) => <Fonte key={i} fonte={f} />)}
          </ul>
        </>
      )}
    </div>
  );
}
