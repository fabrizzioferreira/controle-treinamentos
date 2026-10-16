from __future__ import annotations

import pytest

from backend.src.controle_treinamentos.application.financeiro_produtividade_funcao import (
    resolver_funcao_produtividade,
)


@pytest.mark.parametrize("nome", ["Andre Affonso Abdalla", "Paulo Abdala", "André Affonso Abdalla"])
def test_resolver_funcao_produtividade_mantem_abdalla_como_copiloto(nome):
    assert resolver_funcao_produtividade({"tripulante_nome": nome, "funcao": "comandante"}) == "copiloto"


def test_resolver_funcao_produtividade_nao_aplica_excecao_para_agnello():
    assert resolver_funcao_produtividade({"tripulante_nome": "Rafael Leao Agnello", "funcao": "comandante"}) == "comandante"
