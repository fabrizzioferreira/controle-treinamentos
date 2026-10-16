from __future__ import annotations

import re
import unicodedata


_COPILOTO_PRODUTIVIDADE_NOMES = ("abdalla", "abdala")


def _text(value) -> str:
    return str(value or "").strip()


def _normalize_name(value) -> str:
    raw = unicodedata.normalize("NFKD", _text(value))
    without_accents = "".join(char for char in raw if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents).strip().lower()


def _is_copiloto_produtividade_excepcional(row: dict) -> bool:
    normalized_name = _normalize_name(row.get("nome") or row.get("tripulante_nome"))
    return any(name in normalized_name for name in _COPILOTO_PRODUTIVIDADE_NOMES)


def resolver_funcao_produtividade(row: dict) -> str:
    if _is_copiloto_produtividade_excepcional(row):
        return "copiloto"
    raw_value = row.get("funcao") or row.get("funcao_operacional") or row.get("tripulante_funcao_operacional")
    return _text(raw_value).lower()


def resolver_categoria_produtividade(row: dict) -> str:
    return _text(row.get("tripulante_categoria_operacional") or row.get("categoria_operacional"))
