"""Funções pequenas de texto usadas em vários módulos."""
from __future__ import annotations

import re
import unicodedata


def sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e com espaços simples. Usado em buscas e comparações."""
    return re.sub(r"\s+", " ", sem_acentos(texto).lower()).strip()


def slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", sem_acentos(texto).lower()).strip("-") or "doc"
