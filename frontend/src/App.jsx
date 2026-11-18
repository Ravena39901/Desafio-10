import { useCallback, useEffect, useRef, useState } from "react";
import { documentos as buscarDocumentos, perguntar } from "./api.js";
import Documentos from "./components/Documentos.jsx";
import Mensagem from "./components/Mensagem.jsx";

const EXEMPLOS = [
  "Quantas faltas posso ter?",
  "Como faço o trancamento da matrícula?",
  "Qual a nota mínima para aprovação?",
  "Quem ganhou a Copa do Mundo de 2022?",
];

export default function App() {
  const [mensagens, setMensagens] = useState([]);
  const [texto, setTexto] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [docs, setDocs] = useState([]);
  const fim = useRef(null);

  const atualizarDocs = useCallback(() => {
    buscarDocumentos().then((d) => setDocs(d.documentos)).catch(() => setDocs([]));
  }, []);

  useEffect(atualizarDocs, [atualizarDocs]);
  useEffect(() => fim.current?.scrollIntoView({ behavior: "smooth" }), [mensagens, carregando]);

  async function enviar(pergunta) {
    const p = pergunta.trim();
    if (!p || carregando) return;
    setTexto("");
    setMensagens((m) => [...m, { papel: "aluno", texto: p }]);
    setCarregando(true);
    try {
      const resposta = await perguntar(p);
      setMensagens((m) => [...m, { papel: "assistente", resposta }]);
    } catch (erro) {
      setMensagens((m) => [...m, { papel: "assistente", erro: erro.message }]);
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="layout">
      <main className="chat">
        <header>
          <h1>Assistente do Regulamento Acadêmico</h1>
          <p>Respostas baseadas somente nos PDFs, com artigo e página. Se não achar, eu aviso.</p>
        </header>

        <div className="mensagens">
          {mensagens.length === 0 && (
            <div className="exemplos">
              <p>Experimente perguntar:</p>
              {EXEMPLOS.map((e) => (
                <button key={e} className="exemplo" onClick={() => enviar(e)}>{e}</button>
              ))}
            </div>
          )}
          {mensagens.map((m, i) => <Mensagem key={i} mensagem={m} />)}
          {carregando && <div className="msg assistente digitando">Buscando no regulamento…</div>}
          <div ref={fim} />
        </div>

        <form className="entrada" onSubmit={(e) => { e.preventDefault(); enviar(texto); }}>
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            placeholder="Escreva sua dúvida…"
            maxLength={500}
            aria-label="Pergunta"
          />
          <button type="submit" disabled={carregando || texto.trim().length < 3}>Perguntar</button>
        </form>
      </main>
      <Documentos documentos={docs} aoAtualizar={atualizarDocs} />
    </div>
  );
}
