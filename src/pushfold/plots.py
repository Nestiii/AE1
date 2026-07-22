"""
Gráficos del proyecto.

    - convergence_plot: curva de convergencia (obligatoria en la consigna).
    - boxplot_final_fitness: diagrama de caja del fitness final entre corridas.
    - range_grid_plot: la clásica grilla 13x13 de manos coloreada push/fold,
      con opción de marcar las diferencias contra el óptimo analítico.

Todas las funciones aceptan un `ax` de matplotlib (o crean uno) y devuelven el
`Axes`, para poder componerlas en una figura o guardarlas por separado.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Patch, Rectangle
except ImportError:  # pragma: no cover
    plt = None

from .hands import LABELS, RANKS

# Orden de los rangos de mayor a menor para los ejes de la grilla (A ... 2).
_GRID_RANKS = RANKS[::-1]  # "AKQJT98765432"


def _require_mpl():
    if plt is None:  # pragma: no cover
        raise ImportError("matplotlib es necesario para graficar (pip install matplotlib).")


def convergence_plot(
    best_history: Sequence[float],
    mean_history: Optional[Sequence[float]] = None,
    optimum: Optional[float] = None,
    ax=None,
    title: str = "Convergencia del GA (push/fold)",
):
    """Grafica el mejor (y opcionalmente el promedio) fitness por generación."""
    _require_mpl()
    if ax is None:
        _, ax = plt.subplots(figsize=(7, 4.2))

    gens = np.arange(len(best_history))
    ax.plot(gens, best_history, color="#1f77b4", lw=2, label="Mejor de la población")
    if mean_history is not None:
        ax.plot(gens, mean_history, color="#ff7f0e", lw=1.5, ls="--",
                label="Promedio de la población")
    if optimum is not None:
        ax.axhline(optimum, color="#2ca02c", lw=1.5, ls=":",
                   label="Óptimo analítico")

    ax.set_xlabel("Generación")
    ax.set_ylabel("Fitness (BB por mano)")
    ax.set_title(title)
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    return ax


def boxplot_by_budget(
    fitness_by_budget: Sequence[Sequence[float]],
    budgets: Sequence[int],
    optimum: Optional[float] = None,
    ax=None,
    title: str = "Fitness final vs. presupuesto de generaciones",
):
    """Diagrama de caja del fitness final para varios presupuestos de generaciones.

    Cada caja resume las N corridas independientes evaluadas tras `budget`
    generaciones. Al aumentar el presupuesto, la mediana sube hacia el óptimo y
    la dispersión se reduce: el GA es cada vez más confiable.

    Args:
        fitness_by_budget: lista de listas; fitness_by_budget[k] = fitness final
            de cada corrida al presupuesto budgets[k].
        budgets: número de generaciones de cada grupo (para las etiquetas x).
        optimum: si se da, dibuja la línea del óptimo analítico.
    """
    _require_mpl()
    if ax is None:
        _, ax = plt.subplots(figsize=(6.5, 4.2))

    positions = np.arange(1, len(budgets) + 1)
    ax.boxplot(fitness_by_budget, positions=positions, widths=0.55,
               patch_artist=True,
               boxprops=dict(facecolor="#aec7e8", color="#1f77b4"),
               medianprops=dict(color="#d62728", lw=2),
               flierprops=dict(marker="o", markersize=3, alpha=0.5))
    # Puntos individuales con jitter para ver todas las corridas.
    rng = np.random.default_rng(0)
    for pos, vals in zip(positions, fitness_by_budget):
        x = pos + (rng.random(len(vals)) - 0.5) * 0.15
        ax.scatter(x, vals, color="#1f77b4", alpha=0.5, zorder=3, s=18)

    if optimum is not None:
        ax.axhline(optimum, color="#2ca02c", lw=1.5, ls=":", label="Óptimo analítico")
        ax.legend(loc="lower right", fontsize=9)

    ax.set_xticks(positions)
    ax.set_xticklabels([str(b) for b in budgets])
    ax.set_xlabel("Generaciones")
    ax.set_ylabel("Fitness final (BB por mano)")
    ax.set_title(title)
    ax.grid(alpha=0.3, axis="y")
    return ax


def _genome_to_grid(genome: np.ndarray) -> np.ndarray:
    """Convierte el cromosoma (169,) a una grilla 13x13 (fila=carta alta).

    Convención estándar de las charts de póker:
        - diagonal          -> pares (AA arriba-izq. ... 22 abajo-der.)
        - triángulo superior -> suited
        - triángulo inferior -> offsuit
    """
    label_to_val = {lab: int(round(v)) for lab, v in zip(LABELS, np.asarray(genome))}
    grid = np.zeros((13, 13), dtype=int)
    for r in range(13):        # fila -> rango alto
        for c in range(13):    # columna -> rango bajo
            hi, lo = _GRID_RANKS[r], _GRID_RANKS[c]
            if r == c:
                lab = f"{hi}{hi}"
            elif c > r:  # arriba-derecha: la carta de la columna es la más baja
                lab = f"{hi}{lo}s"
            else:
                lab = f"{lo}{hi}o"  # abajo-izq: fila es la carta baja -> hi real es la columna
            grid[r, c] = label_to_val[lab]
    return grid


def range_grid_plot(
    genome: np.ndarray,
    reference: Optional[np.ndarray] = None,
    ax=None,
    title: str = "Rango de push evolucionado",
):
    """Dibuja la grilla 13x13 push (color) / fold (gris).

    Si se pasa `reference` (p.ej. el óptimo analítico), las celdas donde el
    cromosoma difiere del óptimo se marcan con un borde rojo.
    """
    _require_mpl()
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    grid = _genome_to_grid(genome)
    cmap = ListedColormap(["#e8e8e8", "#2ca02c"])  # 0=fold gris, 1=push verde
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=1)

    # Etiquetas de las manos en cada celda.
    for r in range(13):
        for c in range(13):
            hi, lo = _GRID_RANKS[r], _GRID_RANKS[c]
            if r == c:
                lab = f"{hi}{hi}"
            elif c > r:
                lab = f"{hi}{lo}s"
            else:
                lab = f"{lo}{hi}o"
            ax.text(c, r, lab, ha="center", va="center", fontsize=6.5,
                    color="black")

    # Marcar diferencias contra la referencia.
    if reference is not None:
        ref_grid = _genome_to_grid(reference)
        diff = np.argwhere(grid != ref_grid)
        for r, c in diff:
            ax.add_patch(Rectangle((c - 0.5, r - 0.5), 1, 1, fill=False,
                                   edgecolor="#d62728", lw=2.5))

    ax.set_xticks(range(13))
    ax.set_yticks(range(13))
    ax.set_xticklabels(list(_GRID_RANKS), fontsize=8)
    ax.set_yticklabels(list(_GRID_RANKS), fontsize=8)
    ax.set_xlabel("Carta baja")
    ax.set_ylabel("Carta alta")
    ax.set_title(title)

    legend = [Patch(facecolor="#2ca02c", label="Push (all-in)"),
              Patch(facecolor="#e8e8e8", label="Fold")]
    if reference is not None:
        legend.append(Patch(facecolor="none", edgecolor="#d62728",
                            label="Difiere del óptimo"))
    ax.legend(handles=legend, loc="upper center", bbox_to_anchor=(0.5, -0.08),
              ncol=3, fontsize=8, frameon=False)
    return ax
