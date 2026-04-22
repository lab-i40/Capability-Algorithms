"""Helpers para resolver diretorios de relatorio por modelo."""

from __future__ import annotations

import os
import re
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[2]
_REPORTS_ROOT = _ROOT_DIR / "reports"
_INVALID_SLUG_CHARS = re.compile(r"[^A-Za-z0-9._-]")
_FALLBACK_MODEL_SLUG = "unknown_model"


def slugify_model(name: str) -> str:
    """
    Normaliza o nome do modelo para uso em nome de diretorio.

    Regras:
    - troca '/' e espacos por '_'
    - troca qualquer caractere fora de [A-Za-z0-9._-] por '_'
    """
    if not isinstance(name, str):
        raise TypeError(f"name precisa ser str, recebido: {type(name).__name__}")

    stripped_name = name.strip()
    if not stripped_name:
        return _FALLBACK_MODEL_SLUG

    sanitized = stripped_name.replace("/", "_").replace(" ", "_")
    return _INVALID_SLUG_CHARS.sub("_", sanitized)


def report_dir_for_model(model_name: str | None) -> Path:
    """Retorna `reports/<slug(model_name)>`."""
    raw_model = model_name if model_name is not None else _FALLBACK_MODEL_SLUG
    return _REPORTS_ROOT / slugify_model(raw_model)


def current_report_dir() -> Path:
    """Retorna `reports/<slug(LLM_MODEL)>` para o ambiente atual."""
    return report_dir_for_model(os.getenv("LLM_MODEL"))
