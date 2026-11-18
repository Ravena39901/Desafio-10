"""Lista os modelos do Gemini disponíveis para a sua chave (os nomes mudam com o tempo).

Uso (dentro da pasta backend):  python -m scripts.listar_modelos
Copie o nome desejado para GENERATION_MODEL / EMBEDDING_MODEL no .env (sem o prefixo "models/").
"""
from __future__ import annotations

from app.config import Settings


def main() -> None:
    chave = Settings.from_env().gemini_api_key
    if not chave:
        raise SystemExit("Defina GEMINI_API_KEY no arquivo .env")
    from google import genai

    cliente = genai.Client(api_key=chave)
    geracao, embeddings = [], []
    for m in cliente.models.list():
        nome = (getattr(m, "name", "") or "").removeprefix("models/")
        acoes = getattr(m, "supported_actions", None) or []
        if "embedContent" in acoes:
            embeddings.append(nome)
        elif "generateContent" in acoes:
            geracao.append(nome)
    print("Modelos de geração de texto:")
    print("\n".join(f"  {n}" for n in sorted(geracao)))
    print("\nModelos de embeddings:")
    print("\n".join(f"  {n}" for n in sorted(embeddings)))


if __name__ == "__main__":
    main()
