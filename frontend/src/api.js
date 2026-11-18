async function pedir(url, opcoes) {
  let resposta;
  try {
    resposta = await fetch(url, opcoes);
  } catch {
    throw new Error("Não consegui falar com o servidor. A API está rodando na porta 8000?");
  }
  const dados = await resposta.json().catch(() => ({}));
  if (!resposta.ok) {
    const detalhe = Array.isArray(dados.detail) ? dados.detail.map((d) => d.msg).join("; ") : dados.detail;
    throw new Error(detalhe || `Erro ${resposta.status}`);
  }
  return dados;
}

export const perguntar = (pergunta) =>
  pedir("/api/perguntar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pergunta }),
  });

export const saude = () => pedir("/api/saude");
export const documentos = () => pedir("/api/documentos");

export function enviarPdfs(arquivos) {
  const form = new FormData();
  for (const a of arquivos) form.append("arquivos", a);
  return pedir("/api/ingestao", { method: "POST", body: form });
}
