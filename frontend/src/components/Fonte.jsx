import { useState } from "react";

export default function Fonte({ fonte }) {
  const [aberta, setAberta] = useState(false);
  const rotulo = [fonte.referencia, `p. ${fonte.paginas}`].join(" · ");
  return (
    <li className="fonte">
      <button className="fonte-cabecalho" onClick={() => setAberta(!aberta)} aria-expanded={aberta}>
        <span className="fonte-rotulo">{rotulo}</span>
        <span className="fonte-arquivo">{fonte.arquivo}</span>
        <span className="fonte-score" title="Similaridade com a pergunta">{Math.round(fonte.score * 100)}%</span>
      </button>
      {fonte.secao && <div className="fonte-secao">{fonte.secao}</div>}
      {aberta && <blockquote className="fonte-trecho">{fonte.trecho}</blockquote>}
    </li>
  );
}
