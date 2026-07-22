"""
Algoritmo Genético (GA) para optimizar el rango de push/fold.

Codificación
------------
Cada individuo es un vector binario de 169 genes (1 = push, 0 = fold), uno por
cada clase de mano inicial. La población es una matriz (pop_size, 169).

Operadores (los clásicos de un GA binario)
------------------------------------------
    - Selección por torneo: se eligen `tournament_size` individuos al azar y
      gana el de mayor fitness. Presión de selección simple y regulable.
    - Cruza uniforme: cada gen del hijo se toma de uno u otro padre al azar
      (con probabilidad `crossover_rate` de cruzar; si no, se clona un padre).
    - Mutación bit-flip: cada gen se invierte con probabilidad `mutation_rate`.
    - Elitismo: los `elitism` mejores pasan intactos a la próxima generación,
      garantizando que el mejor fitness nunca empeore (curva monótona).

Salida
------
`run_ga` devuelve un objeto GAResult con el mejor cromosoma, su fitness y el
historial de mejor/promedio por generación (para el gráfico de convergencia).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

import numpy as np

from .hands import N_HANDS


@dataclass
class GAConfig:
    """Hiperparámetros del GA."""

    pop_size: int = 80
    n_generations: int = 120
    crossover_rate: float = 0.9
    mutation_rate: float = 1.0 / N_HANDS  # ~1 bit esperado por cromosoma
    tournament_size: int = 3
    elitism: int = 2
    seed: int = 0


@dataclass
class GAResult:
    """Resultado de una corrida del GA."""

    best_genome: np.ndarray
    best_fitness: float
    best_history: List[float]   # mejor fitness por generación
    mean_history: List[float]   # fitness promedio por generación
    config: GAConfig


def _tournament_select(
    pop: np.ndarray, fitness: np.ndarray, k: int, rng: np.random.Generator
) -> np.ndarray:
    """Devuelve una copia del ganador de un torneo de tamaño k."""
    idx = rng.integers(0, pop.shape[0], size=k)
    winner = idx[np.argmax(fitness[idx])]
    return pop[winner].copy()


def _uniform_crossover(
    p1: np.ndarray, p2: np.ndarray, rate: float, rng: np.random.Generator
) -> np.ndarray:
    """Cruza uniforme entre dos padres. Con prob. (1-rate) clona a p1."""
    if rng.random() >= rate:
        return p1.copy()
    mask = rng.random(p1.shape[0]) < 0.5
    child = np.where(mask, p1, p2)
    return child.astype(np.int8)


def _mutate(genome: np.ndarray, rate: float, rng: np.random.Generator) -> np.ndarray:
    """Mutación bit-flip: invierte cada gen con probabilidad `rate`."""
    flips = rng.random(genome.shape[0]) < rate
    genome[flips] = 1 - genome[flips]
    return genome


def run_ga(
    fitness_fn: Callable[[np.ndarray], np.ndarray],
    config: GAConfig,
    verbose: bool = False,
) -> GAResult:
    """Ejecuta el GA.

    Args:
        fitness_fn: función que recibe una población (P,169) y devuelve un vector
            (P,) de fitness. Típicamente `PushFoldGame.fitness_population`.
        config: hiperparámetros.
        verbose: si True imprime el mejor fitness cada ~10% de generaciones.

    Returns:
        GAResult con el mejor individuo y el historial de convergencia.
    """
    rng = np.random.default_rng(config.seed)

    # Población inicial aleatoria (bits equiprobables).
    pop = (rng.random((config.pop_size, N_HANDS)) < 0.5).astype(np.int8)
    fitness = fitness_fn(pop)

    best_history: List[float] = []
    mean_history: List[float] = []

    best_idx = int(np.argmax(fitness))
    best_genome = pop[best_idx].copy()
    best_fitness = float(fitness[best_idx])

    for gen in range(config.n_generations):
        # --- Registro de estadísticas de la generación actual ---
        gen_best_idx = int(np.argmax(fitness))
        if fitness[gen_best_idx] > best_fitness:
            best_fitness = float(fitness[gen_best_idx])
            best_genome = pop[gen_best_idx].copy()
        best_history.append(best_fitness)
        mean_history.append(float(fitness.mean()))

        # --- Nueva generación ---
        new_pop = np.empty_like(pop)

        # Elitismo: pasan los mejores sin tocar.
        if config.elitism > 0:
            elite_idx = np.argsort(-fitness)[: config.elitism]
            new_pop[: config.elitism] = pop[elite_idx]

        # Resto por selección + cruza + mutación.
        for i in range(config.elitism, config.pop_size):
            p1 = _tournament_select(pop, fitness, config.tournament_size, rng)
            p2 = _tournament_select(pop, fitness, config.tournament_size, rng)
            child = _uniform_crossover(p1, p2, config.crossover_rate, rng)
            child = _mutate(child, config.mutation_rate, rng)
            new_pop[i] = child

        pop = new_pop
        fitness = fitness_fn(pop)

        if verbose and (gen % max(1, config.n_generations // 10) == 0):
            print(f"  gen {gen:4d}: best={best_fitness:.5f} mean={mean_history[-1]:.5f}")

    # Estadística de la última generación ya evolucionada.
    gen_best_idx = int(np.argmax(fitness))
    if fitness[gen_best_idx] > best_fitness:
        best_fitness = float(fitness[gen_best_idx])
        best_genome = pop[gen_best_idx].copy()
    best_history.append(best_fitness)
    mean_history.append(float(fitness.mean()))

    return GAResult(
        best_genome=best_genome,
        best_fitness=best_fitness,
        best_history=best_history,
        mean_history=mean_history,
        config=config,
    )
