"""
Matriz de equity all-in preflop entre las 169 clases de mano.

`equity[i][j]` = probabilidad de que la clase de mano `i` (héroe) gane el
showdown contra la clase `j` (villano) si ambos van all-in preflop y se reparten
las 5 cartas comunitarias, contando los empates como media victoria.

Cómo se calcula
---------------
Para cada par de clases (i, j) estimamos la equity por Monte Carlo:

    1. Se elige un combo concreto al azar de la clase i (p.ej. AhAd para "AA").
    2. Se elige un combo concreto al azar de la clase j que no comparta cartas.
    3. Se reparten 5 cartas de board del resto del mazo.
    4. Se evalúan las dos manos de 7 cartas con eval7 y se cuenta win/tie.

Muestrear también los combos (y no solo el board) hace que el "card removal"
—el hecho de que las cartas del héroe no pueden estar en la mano del villano—
quede reflejado sin sesgo. Usamos dos simetrías para abaratar el cómputo:

    - equity[i][i] = 0.5   (misma clase en ambos lados -> simétrico)
    - equity[j][i] = 1 - equity[i][j]

con lo que solo hace falta calcular el triángulo superior (14.196 matchups).

El resultado se cachea en disco (`data/equity_169x169.npy`). Ese archivo se
versiona en el repo, así el resto del proyecto (GA y gráficos) corre sin
necesidad de tener eval7 instalado. `eval7` solo hace falta para regenerarlo.
"""

from __future__ import annotations

import os

import numpy as np

from .hands import N_HANDS, combos_of

# Ubicación por defecto del cache (…/AE1/data/equity_169x169.npy).
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))
DEFAULT_CACHE = os.path.join(_PROJECT_ROOT, "data", "equity_169x169.npy")


def load_equity_matrix(path: str = DEFAULT_CACHE) -> np.ndarray:
    """Carga la matriz de equity cacheada. Falla si no existe (usar precompute)."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No se encontró la matriz de equity en {path}. "
            "Generala con scripts/precompute_equity.py (requiere eval7)."
        )
    matrix = np.load(path)
    if matrix.shape != (N_HANDS, N_HANDS):
        raise ValueError(f"Forma inesperada {matrix.shape}, se esperaba {(N_HANDS, N_HANDS)}")
    return matrix.astype(np.float64)


def compute_equity_matrix(
    n_samples: int = 25000,
    seed: int = 42,  # aceptado por compatibilidad; ver nota sobre el RNG de eval7.
    progress: bool = True,
) -> np.ndarray:
    """Calcula la matriz 169x169 de equity por Monte Carlo. Requiere `eval7`.

    Estrategia (rápida y auto-consistente):
        Para cada par ordenado de clases (i, j) tomamos un combo representativo
        de la clase i (héroe) y el rango completo de la clase j (villano), y
        estimamos la equity con el Monte Carlo en C de eval7
        (`py_hand_vs_range_monte_carlo`). Ese motor reparte las 5 comunitarias y
        promedia sobre los combos del rango del villano descartando los que
        comparten cartas con el héroe (card removal correcto).

        Se calculan los 169*168 pares ordenados directamente (no se asume
        simetría) y la diagonal se fija en 0.5 por simetría exacta (misma clase
        en ambos lados). El resultado es E[i][j] = P(gana la clase i vs la j).

    Nota sobre reproducibilidad: eval7 usa su propio RNG interno (xorshift), así
    que `seed` se acepta por compatibilidad pero no fija la secuencia. Con
    n_samples grande el ruido es ~1/sqrt(n) (≈0.003 con 25000) y despreciable.
    Como el GA y el óptimo analítico se calculan sobre ESTA misma matriz, la
    validación es exacta cualquiera sea el pequeño ruido de estimación.

    Args:
        n_samples: iteraciones Monte Carlo por matchup (default 25000).
        seed: ver nota (no afecta el RNG de eval7).
        progress: si True imprime avance cada ~10% de las filas.

    Returns:
        Matriz (169, 169) de float64 con las equities.
    """
    try:
        import eval7
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Se necesita 'eval7' para calcular la matriz. Instalar con "
            "`pip install eval7` (o `pip install --no-build-isolation eval7`)."
        ) from exc

    # Combo representativo (primer combo) de cada clase, como eval7.Card.
    hero_combo = [[eval7.Card(c) for c in combos_of(i)[0]] for i in range(N_HANDS)]
    # Rango completo de cada clase como eval7.HandRange (para el villano).
    from .hands import LABELS
    villain_range = [eval7.HandRange(LABELS[j]) for j in range(N_HANDS)]

    matrix = np.full((N_HANDS, N_HANDS), 0.5, dtype=np.float64)
    mc = eval7.py_hand_vs_range_monte_carlo

    for i in range(N_HANDS):
        for j in range(N_HANDS):
            if i == j:
                continue  # diagonal = 0.5 (ya inicializada)
            matrix[i, j] = mc(hero_combo[i], villain_range[j], [], n_samples)
        if progress and (i % 17 == 0 or i == N_HANDS - 1):
            pct = 100.0 * (i + 1) / N_HANDS
            print(f"  equity: fila {i + 1}/{N_HANDS} ({pct:4.0f}%)", flush=True)

    return matrix


def save_equity_matrix(matrix: np.ndarray, path: str = DEFAULT_CACHE) -> None:
    """Guarda la matriz en `path` (crea el directorio si hace falta)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, matrix.astype(np.float32))  # float32 alcanza y pesa la mitad.
    print(f"Matriz guardada en {path} ({matrix.shape}, {matrix.dtype} -> float32)")


def get_equity_matrix(
    path: str = DEFAULT_CACHE,
    n_samples: int = 4000,
    seed: int = 42,
) -> np.ndarray:
    """Devuelve la matriz: la carga del cache si existe, o la calcula y cachea."""
    if os.path.exists(path):
        return load_equity_matrix(path)
    print("Cache no encontrado: calculando la matriz de equity (una sola vez)...")
    matrix = compute_equity_matrix(n_samples=n_samples, seed=seed)
    save_equity_matrix(matrix, path)
    return matrix
