from __future__ import annotations

from app import config


def test_env_ignora_comentario_na_mesma_linha(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        'PROVIDER=gemini                 # gemini | local\n'
        'GENERATION_MODEL=gemini-flash-latest   # confira\n'
        'CHAVE_COM_ASPAS="abc # nao e comentario"\n'
        'CHAVE_COM_HASH=ab#cd\n',
        encoding="utf-8",
    )
    for nome in ("PROVIDER", "GENERATION_MODEL", "CHAVE_COM_ASPAS", "CHAVE_COM_HASH"):
        monkeypatch.delenv(nome, raising=False)
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    config._carregar_dotenv()
    import os

    assert os.environ["PROVIDER"] == "gemini"
    assert os.environ["GENERATION_MODEL"] == "gemini-flash-latest"
    assert os.environ["CHAVE_COM_ASPAS"] == "abc # nao e comentario"
    assert os.environ["CHAVE_COM_HASH"] == "ab#cd"
    for nome in ("PROVIDER", "GENERATION_MODEL", "CHAVE_COM_ASPAS", "CHAVE_COM_HASH"):
        monkeypatch.delenv(nome, raising=False)
