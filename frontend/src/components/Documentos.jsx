import { useRef, useState } from "react";
import { enviarPdfs } from "../api.js";

export default function Documentos({ documentos, aoAtualizar }) {
  const entrada = useRef(null);
  const [enviando, setEnviando] = useState(false);
  const [aviso, setAviso] = useState("");

  async function aoEscolher(e) {
    const arquivos = Array.from(e.target.files);
    if (!arquivos.length) return;
    setEnviando(true);
    setAviso("");
    try {
      const r = await enviarPdfs(arquivos);
      setAviso(Object.entries(r.indexados).map(([n, t]) => `${n}: ${t} trechos`).join(" · "));
      aoAtualizar();
    } catch (erro) {
      setAviso(erro.message);
    } finally {
      setEnviando(false);
      e.target.value = "";
    }
  }

  return (
    <aside className="documentos">
      <h3>Documentos indexados</h3>
      {documentos.length === 0 && <p className="vazio">Nenhum PDF indexado ainda.</p>}
      <ul>
        {documentos.map((d) => (
          <li key={d.arquivo}>
            <strong>{d.arquivo}</strong>
            <span>{d.trechos} trechos · {d.paginas} páginas</span>
          </li>
        ))}
      </ul>
      <input ref={entrada} type="file" accept="application/pdf" multiple hidden onChange={aoEscolher} />
      <button className="secundario" onClick={() => entrada.current.click()} disabled={enviando}>
        {enviando ? "Indexando…" : "Enviar PDF"}
      </button>
      {aviso && <p className="aviso">{aviso}</p>}
    </aside>
  );
}
