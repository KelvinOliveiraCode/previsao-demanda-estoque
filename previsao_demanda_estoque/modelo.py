"""Previsão de demanda e plano de reposição de estoque.

Gera uma série temporal sintética de vendas, treina um modelo de regressão
sazonal simples com scikit-learn (sem dependência externa de Prophet),
prevê a demanda futura e gera um plano de reposição.

O pipeline é determinístico: para um mesmo ``random_state`` a série gerada,
o modelo treinado, a previsão e o plano de reposição são idênticos.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from typing import List

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

RANDOM_STATE = 42
HORIZON_DIAS = 30
TEST_SIZE = 0.2


@dataclass(frozen=True)
class Venda:
    """Uma venda registrada em uma data."""

    data: date
    quantidade: int


@dataclass(frozen=True)
class Previsao:
    """Previsão de demanda para uma data futura."""

    data: date
    demanda_prevista: float


@dataclass(frozen=True)
class ItemReposicao:
    """Item do plano de reposição de estoque.

    ``estoque_projetado`` é o estoque disponível estimado para a data, antes
    da reposição. ``quantidade_sugerida`` é a quantidade a comprar para
    cobrir a demanda prevista mais o estoque de segurança.
    """

    produto: str
    data: date
    demanda_prevista: float
    estoque_projetado: int
    estoque_seguranca: int
    quantidade_sugerida: int


@dataclass
class ResultadoModelo:
    """Resultado do treinamento, previsão e planejamento de reposição."""

    mae: float
    previsoes: List[Previsao]
    plano_reposicao: List[ItemReposicao]


def gerar_serie_sintetica(
    *,
    data_inicio: date = date(2024, 1, 1),
    dias: int = 365,
    produto: str = "SKU-001",
    random_state: int = RANDOM_STATE,
) -> List[Venda]:
    """Gera série temporal sintética de vendas.

    Combina tendência de crescimento, sazonalidade semanal e mensal e ruído
    gaussiano. Determinístico para um mesmo ``random_state``.

    Args:
        data_inicio: primeira data da série.
        dias: quantidade de dias a gerar.
        produto: identificador do produto (metadados da série).
        random_state: semente do gerador de números aleatórios.

    Returns:
        Lista de vendas ordenadas por data.
    """
    rng = np.random.default_rng(random_state)
    vendas: List[Venda] = []
    base = 50.0
    for i in range(dias):
        data = data_inicio + timedelta(days=i)
        tendencia = 0.05 * i
        semanal = 10.0 * np.sin(2.0 * np.pi * i / 7.0)
        mensal = 8.0 * np.sin(2.0 * np.pi * i / 30.0)
        media = base + tendencia + semanal + mensal
        quantidade = int(round(max(0.0, float(rng.normal(loc=media, scale=5.0)))))
        vendas.append(Venda(data=data, quantidade=quantidade))
    return vendas


def _ordenar(vendas: List[Venda]) -> List[Venda]:
    return sorted(vendas, key=lambda v: v.data)


def _extrair_features(vendas: List[Venda]) -> tuple[np.ndarray, np.ndarray]:
    """Converte vendas em matriz de features X e vetor alvo y.

    Features: índice temporal, dia da semana, mês, dia do ano, lag-1, lag-7
    e média móvel de 7 dias. Não há vazamento do futuro: cada linha usa apenas
    dados até o próprio dia.
    """
    dados = _ordenar(vendas)
    quantidades = [v.quantidade for v in dados]
    X: List[List[float]] = []
    y: List[float] = []
    for i, venda in enumerate(dados):
        d = venda.data
        dia_ano = d.timetuple().tm_yday
        lag1 = float(quantidades[i - 1]) if i >= 1 else float(quantidades[0])
        lag7 = float(quantidades[i - 7]) if i >= 7 else float(quantidades[0])
        media7 = float(np.mean(quantidades[max(0, i - 6) : i + 1]))
        X.append(
            [
                float(i),
                float(d.weekday()),
                float(d.month),
                float(dia_ano),
                lag1,
                lag7,
                media7,
            ]
        )
        y.append(float(venda.quantidade))
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def _features_futuro(indice: int, data: date, historico: List[float]) -> np.ndarray:
    """Monta o vetor de features para um dia futuro a partir do histórico."""
    lag1 = float(historico[-1])
    lag7 = float(historico[-7]) if len(historico) >= 7 else float(historico[-1])
    media7 = float(np.mean(historico[-7:]))
    return np.asarray(
        [
            float(indice),
            float(data.weekday()),
            float(data.month),
            float(data.timetuple().tm_yday),
            lag1,
            lag7,
            media7,
        ],
        dtype=float,
    ).reshape(1, -1)


def treinar_e_prever(
    vendas: List[Venda],
    *,
    produto: str = "SKU-001",
    dias_futuro: int = HORIZON_DIAS,
    estoque_atual: int = 100,
    estoque_seguranca: int = 20,
    random_state: int = RANDOM_STATE,
    test_size: float = TEST_SIZE,
) -> ResultadoModelo:
    """Treina o modelo, reporta MAE, prevê demanda e planeja reposição.

    O split é temporal (sem embaralhamento) para respeitar a ordem da série.
    O MAE é calculado sobre a parte de teste e reportado em
    ``ResultadoModelo.mae``.

    Args:
        vendas: série histórica de vendas.
        produto: identificador do produto no plano de reposição.
        dias_futuro: horizonte de previsão em dias.
        estoque_atual: estoque disponível hoje.
        estoque_seguranca: estoque de segurança a manter.
        random_state: semente para treino determinístico.
        test_size: fração da série reservada para teste.

    Returns:
        Resultado com MAE, previsões futuras e plano de reposição.

    Raises:
        ValueError: se a série for insuficiente para treinar.
    """
    if len(vendas) < 14:
        raise ValueError("série insuficiente para treinar (mínimo de 14 pontos)")

    X, y = _extrair_features(vendas)
    corte = int(len(X) * (1.0 - test_size))
    X_treino, X_teste = X[:corte], X[corte:]
    y_treino, y_teste = y[:corte], y[corte:]

    modelo = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=random_state,
    )
    modelo.fit(X_treino, y_treino)

    y_predito = modelo.predict(X_teste)
    mae = float(mean_absolute_error(y_teste, y_predito))

    dados = _ordenar(vendas)
    ultimo = dados[-1]
    historico = [float(v.quantidade) for v in dados]
    ultimo_indice = len(dados) - 1

    previsoes: List[Previsao] = []
    for h in range(1, dias_futuro + 1):
        data_futura = ultimo.data + timedelta(days=h)
        x_futuro = _features_futuro(ultimo_indice + h, data_futura, historico)
        demanda = float(max(0.0, modelo.predict(x_futuro)[0]))
        historico.append(demanda)
        previsoes.append(Previsao(data=data_futura, demanda_prevista=demanda))

    plano: List[ItemReposicao] = []
    estoque_projetado = int(estoque_atual)
    for prev in previsoes:
        necessidade = int(math.ceil(prev.demanda_prevista)) + int(estoque_seguranca)
        quantidade_sugerida = max(0, necessidade - estoque_projetado)
        plano.append(
            ItemReposicao(
                produto=produto,
                data=prev.data,
                demanda_prevista=prev.demanda_prevista,
                estoque_projetado=estoque_projetado,
                estoque_seguranca=int(estoque_seguranca),
                quantidade_sugerida=quantidade_sugerida,
            )
        )
        estoque_projetado = (
            estoque_projetado + quantidade_sugerida - int(round(prev.demanda_prevista))
        )

    return ResultadoModelo(mae=mae, previsoes=previsoes, plano_reposicao=plano)
