"""
pushfold — Optimización de un rango de push/fold en póker heads-up con un
Algoritmo Genético (Desafío Práctico de Algoritmos Evolutivos I, MIA-UBA 2026).

Módulos:
    hands   : las 169 clases de mano inicial, pesos y combos.
    equity  : matriz 169x169 de equity all-in preflop (precomputada con eval7).
    game    : modelo del juego push/fold y función de fitness.
    ga      : algoritmo genético binario.
    plots   : gráficos de convergencia, box plot y grilla de rango 13x13.
"""

from .game import PushFoldGame
from .ga import GAConfig, GAResult, run_ga

__all__ = ["PushFoldGame", "GAConfig", "GAResult", "run_ga"]
__version__ = "0.1.0"
