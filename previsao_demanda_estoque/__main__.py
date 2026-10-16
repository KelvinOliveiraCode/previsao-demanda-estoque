"""CLI da previsão de demanda e plano de reposição de estoque."""

from __future__ import annotations

import argparse

from .modelo import gerar_serie_sintetica, treinar_e_prever


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Previsão de demanda e plano de reposição de estoque"
    )
    parser.add_argument("--dias-historico", type=int, default=365)
    parser.add_argument("--dias-futuro", type=int, default=30)
    parser.add_argument("--estoque-atual", type=int, default=100)
    parser.add_argument("--estoque-seguranca", type=int, default=20)
    parser.add_argument("--produto", default="SKU-001")
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    vendas = gerar_serie_sintetica(
        dias=args.dias_historico,
        produto=args.produto,
        random_state=args.random_state,
    )
    resultado = treinar_e_prever(
        vendas,
        produto=args.produto,
        dias_futuro=args.dias_futuro,
        estoque_atual=args.estoque_atual,
        estoque_seguranca=args.estoque_seguranca,
        random_state=args.random_state,
    )
    print(f"Produto: {args.produto}")
    print(f"MAE (erro médio absoluto): {resultado.mae:.2f} unidades")
    print(f"Previsões geradas: {len(resultado.previsoes)} dias")
    print(f"Plano de reposição: {len(resultado.plano_reposicao)} itens")
    total = sum(i.quantidade_sugerida for i in resultado.plano_reposicao)
    print(f"Quantidade total sugerida para reposição: {total} unidades")


if __name__ == "__main__":
    main()
