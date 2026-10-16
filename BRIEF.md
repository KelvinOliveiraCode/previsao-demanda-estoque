# BRIEF — previsao-demanda-estoque

**Projeto:** previsao-demanda-estoque
**Área:** Dados/BI
**Dono da validação:** workflow manager (o autor desta mensagem)

## O que foi entregue

| Item | Caminho |
|------|---------|
| Código do modelo (série sintética, treino, previsão, plano de reposição) | `previsao_demanda_estoque/modelo.py` |
| Pacote / init | `previsao_demanda_estoque/__init__.py` |
| CLI | `previsao_demanda_estoque/__main__.py` |
| Testes pytest | `tests/test_modelo.py` |
| Metadados do projeto | `pyproject.toml` |
| README bilíngue PT-BR + EN | `README.md` |
| Este resumo | `BRIEF.md` |

## Funcionalidade

- Gera série temporal sintética de vendas (tendência + sazonalidade semanal/mensal + ruído), determinística por `random_state` fixo (42).
- Treina regressor scikit-learn (GradientBoostingRegressor) com split temporal; sem dependência externa de Prophet.
- Reporta erro de previsão (MAE) sobre a parte de teste.
- Prevê demanda futura e gera plano de reposição (quantidade sugerida = demanda prevista + estoque de segurança − estoque projetado, sem valores negativos).

## Como verificar

1. Entre na pasta do projeto:
   ```
   cd C:\Users\Kelvin\AppData\Local\Temp\opencode\github-staging\projects\previsao-demanda-estoque
   ```
2. Instale as dependências:
   ```
   pip install -e .
   ```
3. Rode os testes (gate de verificação):
   ```
   python -m pytest -q
   ```
   Esperado: `6 passed`.
4. Confirme o MAE reportado:
   ```
   python -m pytest -q -s
   ```
   Esperado: linha `MAE reportado: ... unidades` e `6 passed`.
5. Execute o CLI:
   ```
   python -m previsao_demanda_estoque --dias-historico 365 --dias-futuro 30 --estoque-atual 100 --estoque-seguranca 20 --produto SKU-001 --random-state 42
   ```

## Critérios de aceitação (do PLANO_50_PROJETOS.md)

- [x] Erro de previsão reportado (MAE, nos testes e no CLI).
- [x] Testes que passem (6 passed, pytest).
- [x] README PT/EN completo (título, descrição, como usar, testes, licença MIT, autor Kelvin Oliveira).
- [x] Código limpo, determinístico, com tipos, docstrings e random_state fixo.

**Resultado dos testes:** 6 passed (suíte verde).
