# Previsão de Demanda e Plano de Reposição de Estoque

## Descrição (PT-BR)

Projeto da área Dados/BI que prevê a demanda futura de um produto e gera um plano de reposição de estoque. Gera uma série temporal sintética de vendas, treina um modelo de regressão com scikit-learn (sem dependência externa de Prophet), prevê a demanda dos próximos dias e calcula a quantidade sugerida para reposição, considerando estoque atual e estoque de segurança.

O erro de previsão (MAE) é reportado no treino e nos testes.

## Description (EN)

Data/BI project that forecasts future product demand and generates a stock replenishment plan. It generates a synthetic sales time series, trains a regression model with scikit-learn (no external Prophet dependency), forecasts demand for the coming days, and computes the suggested replenishment quantity, considering current stock and safety stock.

The forecast error (MAE) is reported during training and in the tests.

## Stack / Pilha

- Python 3.10+
- NumPy
- scikit-learn

## Como usar / How to use

Instale as dependências:

```
pip install -e .
```

Execute a previsão:

```
python -m previsao_demanda_estoque --dias-historico 365 --dias-futuro 30 --estoque-atual 100 --estoque-seguranca 20 --produto SKU-001 --random-state 42
```

Saída de exemplo:

```
Produto: SKU-001
MAE (erro médio absoluto): 4.26 unidades
Previsões geradas: 30 dias
Plano de reposição: 30 itens
Quantidade total sugerida para reposição: 682 unidades
```

## Testes / Tests

Rode a suíte pytest:

```
python -m pytest -q
```

Resultado: 6 passed. O MAE é impresso no stdout (ex.: `MAE reportado: 6.44 unidades`).

## Licença / License

MIT

## Autor / Author

Kelvin Oliveira
