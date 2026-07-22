"""
Modelo del juego push/fold heads-up y función de fitness.

Situación (heads-up = 1 contra 1, stacks cortos)
-------------------------------------------------
Dos jugadores con un stack efectivo de `S` big blinds (BB). El botón / ciega
chica (SB) postea 0.5 BB, la ciega grande (BB) postea 1 BB. Con stacks tan
cortos, la teoría dice que la estrategia óptima de la SB es binaria: **push
(all-in) o fold**. Si la SB va all-in, la BB decide **call o fold**.

Esa decisión "push o fold" para cada una de las 169 manos es exactamente lo que
optimiza el algoritmo genético: un cromosoma de 169 bits (1 = push, 0 = fold).

EV (valor esperado, en BB) de cada resultado desde la óptica de la SB
---------------------------------------------------------------------
    - SB foldea:                       EV = -0.5   (pierde su ciega chica)
    - SB pushea y la BB foldea:        EV = +1.0   (se lleva la ciega grande)
    - SB pushea y la BB paga (all-in): EV = S*(2*eq - 1)
          donde `eq` es la equity del héroe vs la mano del villano. (Ambos ponen
          S; el héroe recupera eq*2S del pozo, arrancó con S -> neto S*(2eq-1).)

Fitness de un cromosoma
-----------------------
Para cada mano h del héroe:

    EV_push(h) = Σ_j w_j * [ call_j * S*(2*eq(h,j)-1) + (1-call_j) * (+1.0) ]
    EV_fold    = -0.5

donde j recorre las 169 clases del villano, w_j es la probabilidad a priori de
esa clase y call_j ∈ {0,1} indica si la BB paga con ella (rango FIJO en esta
versión A1). El fitness total es la ganancia esperada por mano:

    fitness(x) = Σ_h w_h * [ x_h * EV_push(h) + (1-x_h) * EV_fold ]

Como el rango de la BB es fijo, `EV_push(h)` no depende de las demás manos: el
problema es **separable** y su óptimo se conoce analíticamente (push si y solo si
EV_push(h) > EV_fold). Lo usamos como verdad de referencia para validar que el
GA converge al óptimo correcto. (La extensión A2 —coevolucionar el rango de la
BB— rompe esa separabilidad; queda documentada como trabajo futuro.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from .hands import HAND_WEIGHTS, LABELS, N_HANDS

SMALL_BLIND = 0.5
BIG_BLIND = 1.0


@dataclass
class PushFoldGame:
    """Encapsula el modelo: equity, stack, rango de la BB y cálculo de fitness.

    Attributes:
        equity: matriz (169,169) de equities all-in preflop.
        stack_bb: stack efectivo en BB (por defecto 10).
        bb_call_fraction: fracción de las manos más fuertes con las que la BB
            paga (rango fijo del rival). 0.5 = paga con el 50% superior.
    """

    equity: np.ndarray
    stack_bb: float = 10.0
    bb_call_fraction: float = 0.50

    # Derivados (se completan en __post_init__).
    weights: np.ndarray = field(init=False)
    bb_call_mask: np.ndarray = field(init=False)
    ev_push: np.ndarray = field(init=False)
    ev_fold: float = field(init=False)

    def __post_init__(self) -> None:
        if self.equity.shape != (N_HANDS, N_HANDS):
            raise ValueError(f"equity debe ser {(N_HANDS, N_HANDS)}, es {self.equity.shape}")
        self.weights = np.asarray(HAND_WEIGHTS, dtype=np.float64)
        self.bb_call_mask = self._build_bb_call_range(self.bb_call_fraction)
        self.ev_fold = -SMALL_BLIND
        self.ev_push = self._compute_ev_push()

    # ---- Rango de call de la BB (rival fijo) -------------------------------
    def hand_strength(self) -> np.ndarray:
        """Fuerza a priori de cada mano = equity promedio vs una mano al azar.

        strength[i] = Σ_j w_j * equity[i][j]. Sirve para rankear las manos y
        definir con cuáles paga la BB (las más fuertes).
        """
        # Reducción elementwise (equivalente a equity @ weights). Evitamos matmul
        # a propósito: en macOS con Apple Accelerate + numpy 2.0 el matmul emite
        # warnings espurios (divide-by-zero/overflow) pese a dar el resultado
        # correcto. Esta forma no los dispara en ningún backend.
        return (self.equity * self.weights).sum(axis=1)

    def _build_bb_call_range(self, fraction: float) -> np.ndarray:
        """Máscara booleana (169,) de las manos con las que paga la BB.

        La BB paga con las manos más fuertes hasta acumular `fraction` del peso
        total (p.ej. 0.5 -> el 50% de las manos más fuertes, ponderado por
        frecuencia). Es un rival simplificado pero razonable e independiente de
        la SB, lo que mantiene el problema limpio para la versión A1.
        """
        fraction = float(np.clip(fraction, 0.0, 1.0))
        strength = self.hand_strength()
        order = np.argsort(-strength)  # de más fuerte a más débil
        mask = np.zeros(N_HANDS, dtype=bool)
        cum = 0.0
        for idx in order:
            if cum >= fraction:
                break
            mask[idx] = True
            cum += self.weights[idx]
        return mask

    # ---- Motor de EV -------------------------------------------------------
    def _compute_ev_push(self) -> np.ndarray:
        """Vector (169,) con el EV de pushear cada mano contra la BB fija.

        Vectorizado: para la mano h, la BB paga con las manos del conjunto C y
        foldea con el resto. Contra las que paga, EV = S*(2*eq-1); contra las que
        foldea, EV = +1 BB (la ciega grande), ponderando por w_j.
        """
        S = self.stack_bb
        w = self.weights
        call = self.bb_call_mask.astype(np.float64)  # (169,)
        fold = 1.0 - call

        # Showdown vs las manos con las que la BB paga.
        showdown = S * (2.0 * self.equity - 1.0)      # (169,169): héroe h vs villano j
        # Reducción elementwise (equivalente a showdown @ (w*call)); ver nota en
        # hand_strength() sobre por qué evitamos matmul.
        ev_when_called = (showdown * (w * call)).sum(axis=1)  # (169,)
        # La BB foldea -> ganamos la ciega grande, con prob = peso de esas manos.
        ev_when_folded = BIG_BLIND * float((w * fold).sum())
        return ev_when_called + ev_when_folded

    # ---- Fitness -----------------------------------------------------------
    def fitness(self, genome: np.ndarray) -> float:
        """Fitness (BB/mano) de un cromosoma (169 bits push/fold)."""
        genome = np.asarray(genome, dtype=np.float64)
        per_hand = genome * self.ev_push + (1.0 - genome) * self.ev_fold
        return float((self.weights * per_hand).sum())

    def fitness_population(self, pop: np.ndarray) -> np.ndarray:
        """Fitness vectorizado de una población (P,169) -> vector (P,)."""
        pop = np.asarray(pop, dtype=np.float64)
        # Contribución por mano según se pushee (ev_push) o se foldee (ev_fold).
        contrib = pop * (self.weights * self.ev_push) + (1.0 - pop) * (
            self.weights * self.ev_fold
        )
        return contrib.sum(axis=1)

    # ---- Óptimo analítico (verdad de referencia) ---------------------------
    def analytical_optimum(self) -> np.ndarray:
        """Cromosoma óptimo exacto: push sii EV_push(h) > EV_fold."""
        return (self.ev_push > self.ev_fold).astype(np.int8)

    def optimum_fitness(self) -> float:
        """Fitness del óptimo analítico."""
        return self.fitness(self.analytical_optimum())

    # ---- Utilidades --------------------------------------------------------
    def range_labels(self, genome: np.ndarray) -> list:
        """Lista de etiquetas de las manos que el cromosoma decide pushear."""
        genome = np.asarray(genome).astype(bool)
        return [LABELS[i] for i in range(N_HANDS) if genome[i]]

    def push_percentage(self, genome: np.ndarray) -> float:
        """Porcentaje del total de manos (ponderado por frecuencia) que se pushea."""
        genome = np.asarray(genome, dtype=np.float64)
        return 100.0 * float((self.weights * genome).sum())
