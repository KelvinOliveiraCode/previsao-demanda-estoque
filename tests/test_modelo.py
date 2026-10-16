"""Suíte de testes da previsão de demanda e plano de reposição de estoque."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from previsao_demanda_estoque import (
    HORIZON_DIAS,
    RANDOM_STATE,
    gerar_serie_sintetica,
    treinar_e_prever,
)


@pytest.fixture
def vendas() -> list:
    return gerar_serie_sintetica(dias=200, random_state=RANDOM_STATE)


def test_gerar_serie_sintetica(vendas: list) -> None:
    assert len(vendas) == 200
    assert vendas[0].data == date(2024, 1, 1)
    assert vendas[-1].data == date(2024, 7, 18)
    assert all(v.quantidade >= 0 for v in vendas)


def test_serie_eh_deterministica() -> None:
    a = gerar_serie_sintetica(dias=100, random_state=RANDOM_STATE)
    b = gerar_serie_sintetica(dias=100, random_state=RANDOM_STATE)
    assert [v.quantidade for v in a] == [v.quantidade for v in b]


def test_mae_reportado_e_razoavel(vendas: list) -> None:
    resultado = treinar_e_prever(
        vendas, dias_futuro=HORIZON_DIAS, random_state=RANDOM_STATE
    )
    assert resultado.mae >= 0.0
    assert resultado.mae < 15.0, f"MAE elevado: {resultado.mae:.4f}"
    # reporta o erro de previsão no stdout
    print(f"MAE reportado: {resultado.mae:.4f} unidades")


def test_previsoes_futuras(vendas: list) -> None:
    resultado = treinar_e_prever(
        vendas, dias_futuro=HORIZON_DIAS, random_state=RANDOM_STATE
    )
    assert len(resultado.previsoes) == HORIZON_DIAS
    primeira_esperada = vendas[-1].data + timedelta(days=1)
    assert resultado.previsoes[0].data == primeira_esperada
    assert resultado.previsoes[-1].data == vendas[-1].data + timedelta(days=HORIZON_DIAS)
    assert all(p.demanda_prevista >= 0.0 for p in resultado.previsoes)


def test_plano_reposicao_sem_negativo(vendas: list) -> None:
    resultado = treinar_e_prever(
        vendas,
        dias_futuro=HORIZON_DIAS,
        estoque_atual=200,
        estoque_seguranca=20,
        random_state=RANDOM_STATE,
    )
    assert len(resultado.plano_reposicao) == HORIZON_DIAS
    assert all(i.quantidade_sugerida >= 0 for i in resultado.plano_reposicao)
    assert all(i.estoque_projetado >= 0 for i in resultado.plano_reposicao)
    primeiro = resultado.plano_reposicao[0]
    assert primeiro.quantidade_sugerida == 0


def test_serie_insuficiente_erro() -> None:
    poucas = gerar_serie_sintetica(dias=5, random_state=RANDOM_STATE)
    with pytest.raises(ValueError):
        treinar_e_prever(poucas, dias_futuro=7, random_state=RANDOM_STATE)
