#!/usr/bin/env python3
"""
Corre el GA de push/fold y genera todas las figuras del trabajo.

Uso:
    python scripts/run_ga.py [--stack 10] [--bb-call 0.5] [--runs 30] \
                             [--generations 120] [--pop 80]

Produce en results/:
    convergencia.png   - curva de convergencia (best + promedio + óptimo)
    boxplot.png        - fitness final en N corridas independientes
    rango.png          - grilla 13x13 del rango de push evolucionado

Requiere que exista data/equity_169x169.npy (ver scripts/precompute_equity.py).
Este script NO necesita eval7.
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from pushfold.equity import get_equity_matrix
from pushfold.ga import GAConfig, run_ga
from pushfold.game import PushFoldGame
from pushfold.plots import boxplot_by_budget, convergence_plot, range_grid_plot

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stack", type=float, default=10.0, help="stack efectivo en BB")
    parser.add_argument("--bb-call", type=float, default=0.5,
                        help="fracción de manos con las que paga la BB (0-1)")
    parser.add_argument("--runs", type=int, default=30,
                        help="corridas independientes para el box plot")
    parser.add_argument("--generations", type=int, default=120)
    parser.add_argument("--pop", type=int, default=80)
    args = parser.parse_args()

    import matplotlib
    matplotlib.use("Agg")  # backend sin ventana, para guardar PNGs.
    import matplotlib.pyplot as plt

    os.makedirs(RESULTS_DIR, exist_ok=True)

    # 1) Modelo del juego.
    equity = get_equity_matrix()
    game = PushFoldGame(equity=equity, stack_bb=args.stack, bb_call_fraction=args.bb_call)
    opt_fit = game.optimum_fitness()
    opt_genome = game.analytical_optimum()
    print(f"Óptimo analítico: fitness={opt_fit:.5f} BB/mano, "
          f"push={game.push_percentage(opt_genome):.1f}% de las manos")

    # 2) N corridas independientes (distinta semilla). Guardamos el historial de
    #    cada una: como el mejor fitness es monótono (elitismo), best_history[b]
    #    es el fitness final si hubiéramos parado en la generación b. Eso permite
    #    armar el box plot por presupuesto sin re-correr el GA.
    histories = []
    for r in range(args.runs):
        res = run_ga(game.fitness_population,
                     GAConfig(pop_size=args.pop, n_generations=args.generations, seed=r),
                     verbose=(r == 0))
        histories.append(np.asarray(res.best_history))
    histories = np.vstack(histories)  # (runs, generations+1)

    # Corrida principal (semilla 0) para la curva de convergencia y el rango.
    result = run_ga(game.fitness_population,
                    GAConfig(pop_size=args.pop, n_generations=args.generations, seed=0))
    print(f"GA (corrida principal): best={result.best_fitness:.5f} BB/mano, "
          f"push={game.push_percentage(result.best_genome):.1f}%")
    n_diff = int(np.sum(result.best_genome != opt_genome))
    print(f"Diferencias con el óptimo analítico: {n_diff}/169 manos")

    finals = histories[:, -1]
    print(f"Box plot: {args.runs} corridas, fitness final "
          f"media={finals.mean():.5f}, min={finals.min():.5f}, max={finals.max():.5f}")

    # 3) Figuras.
    ax = convergence_plot(result.best_history, result.mean_history, optimum=opt_fit)
    ax.figure.tight_layout()
    ax.figure.savefig(os.path.join(RESULTS_DIR, "convergencia.png"), dpi=150)
    plt.close(ax.figure)

    # Presupuestos de generaciones para el box plot (acotados al máximo corrido).
    budgets = [b for b in (15, 30, 60, args.generations) if b <= args.generations]
    budgets = sorted(set(budgets))
    fitness_by_budget = [histories[:, b].tolist() for b in budgets]
    ax = boxplot_by_budget(fitness_by_budget, budgets, optimum=opt_fit)
    ax.figure.tight_layout()
    ax.figure.savefig(os.path.join(RESULTS_DIR, "boxplot.png"), dpi=150)
    plt.close(ax.figure)

    ax = range_grid_plot(result.best_genome, reference=opt_genome,
                         title=f"Rango de push evolucionado (stack {args.stack:.0f} BB)")
    ax.figure.tight_layout()
    ax.figure.savefig(os.path.join(RESULTS_DIR, "rango.png"), dpi=150)
    plt.close(ax.figure)

    print(f"Figuras guardadas en {os.path.abspath(RESULTS_DIR)}")


if __name__ == "__main__":
    main()
