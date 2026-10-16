from __future__ import annotations

import unicodedata

CANONICAL_CATEGORY_A = "categoria a"
CANONICAL_CATEGORY_B = "categoria b"
CANONICAL_CATEGORY_TURBOHELICE_PALMAS = "turbohelice_palmas"


def normalizar_categoria_parametro(value) -> str:
    """Normaliza categoria persistida sem promover abreviacoes legadas a canonicas."""
    return str(value or "").strip().lower()


def _sem_acentos(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def _normalizar_texto_operacional(value) -> str:
    raw = str(value or "").strip().lower()
    normalized = raw.replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    return _sem_acentos(normalized)


def normalizar_categoria_operacional(value) -> str:
    """Aceita entrada operacional legada e resolve para a categoria financeira canonica."""
    raw = str(value or "").strip().lower()
    normalized = raw.replace("_", " ").replace("-", " ")
    normalized = " ".join(normalized.split())
    normalized_ascii = _sem_acentos(normalized)
    if normalized_ascii in {"a", CANONICAL_CATEGORY_A}:
        return CANONICAL_CATEGORY_A
    if normalized_ascii in {"b", CANONICAL_CATEGORY_B}:
        return CANONICAL_CATEGORY_B
    if raw in {"turbohelice_palmas", "turbohelice-palmas"} or normalized_ascii in {
        "turbohelice palmas",
        "turboelice palmas",
        "turbo helice palmas",
        "turbo elice palmas",
        "palmas turbohelice",
        "palmas turboelice",
        "palmas turbo helice",
        "palmas turbo elice",
    }:
        return CANONICAL_CATEGORY_TURBOHELICE_PALMAS
    return normalized or ""


def is_operacao_especial_palmas_turbohelice(value) -> bool:
    """Reconhece a marca operacional legada usada para adicional excepcional de Palmas."""
    normalized_ascii = _normalizar_texto_operacional(value)
    if not normalized_ascii:
        return False
    if normalized_ascii == "palmas":
        return True
    tokens = set(normalized_ascii.split())
    compact = normalized_ascii.replace(" ", "")
    return "palmas" in tokens and (
        "turbohelice" in compact
        or "turboelice" in compact
        or "turbo" in tokens
        or "helice" in tokens
        or "elice" in tokens
    )
