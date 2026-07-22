"""
Representación de las manos iniciales de Texas Hold'em.

En Hold'em cada jugador recibe 2 cartas. Existen C(52,2) = 1326 combinaciones
concretas, pero estratégicamente colapsan en **169 clases** distintas:

    - 13 pares            (AA, KK, ..., 22)          -> 6 combos cada una
    - 78 suited (mismo palo, "s": AKs, AQs, ...)     -> 4 combos cada una
    - 78 offsuit (distinto palo, "o": AKo, AQo, ...) -> 12 combos cada una

    13*6 + 78*4 + 78*12 = 78 + 312 + 936 = 1326  (verificación de consistencia)

Este módulo define el orden canónico de esas 169 clases, sus etiquetas, el peso
(probabilidad de recibir cada clase con una mano al azar) y la lista de combos
concretos de cada clase. Todo lo demás del proyecto indexa las manos con estos
mismos índices 0..168, así que este archivo es la única fuente de verdad.
"""

from __future__ import annotations

from itertools import combinations
from typing import List, Tuple

# Rangos ordenados de menor a mayor. El índice (0..12) es la fuerza del rango.
RANKS = "23456789TJQKA"
SUITS = "cdhs"

N_HANDS = 169


def _build_hand_classes() -> List[dict]:
    """Construye la lista canónica de las 169 clases de mano.

    Orden: primero los 13 pares (de AA a 22), luego las 78 suited y por último
    las 78 offsuit, cada bloque de mayor a menor. El orden exacto no es
    importante para el algoritmo, pero al fijarlo garantizamos que los índices
    sean estables y reproducibles entre módulos y corridas.
    """
    # 13 pares, de AA a 22.
    pairs = [_make_class(r, r, "pair") for r in range(12, -1, -1)]
    # 78 suited y 78 offsuit: para cada combinación de rangos hi > lo.
    suited, offsuit = [], []
    for hi in range(12, -1, -1):
        for lo in range(hi - 1, -1, -1):
            suited.append(_make_class(hi, lo, "suited"))
            offsuit.append(_make_class(hi, lo, "offsuit"))
    return pairs + suited + offsuit


def _make_class(hi: int, lo: int, kind: str) -> dict:
    """Crea el diccionario descriptor de una clase de mano."""
    hi_c, lo_c = RANKS[hi], RANKS[lo]
    if kind == "pair":
        label = f"{hi_c}{hi_c}"
        combos = _pair_combos(hi_c)
    elif kind == "suited":
        label = f"{hi_c}{lo_c}s"
        combos = _suited_combos(hi_c, lo_c)
    elif kind == "offsuit":
        label = f"{hi_c}{lo_c}o"
        combos = _offsuit_combos(hi_c, lo_c)
    else:
        raise ValueError(kind)
    return {"label": label, "kind": kind, "hi": hi, "lo": lo, "combos": combos}


def _pair_combos(r: str) -> List[Tuple[str, str]]:
    """6 combos de un par: todas las parejas de palos distintos."""
    return [(r + s1, r + s2) for s1, s2 in combinations(SUITS, 2)]


def _suited_combos(hi: str, lo: str) -> List[Tuple[str, str]]:
    """4 combos suited: mismo palo para ambas cartas."""
    return [(hi + s, lo + s) for s in SUITS]


def _offsuit_combos(hi: str, lo: str) -> List[Tuple[str, str]]:
    """12 combos offsuit: palos distintos entre las dos cartas."""
    return [(hi + s1, lo + s2) for s1 in SUITS for s2 in SUITS if s1 != s2]


# Lista canónica y estructuras derivadas, construidas una sola vez al importar.
HAND_CLASSES: List[dict] = _build_hand_classes()
LABELS: List[str] = [h["label"] for h in HAND_CLASSES]
LABEL_TO_INDEX = {lab: i for i, lab in enumerate(LABELS)}

# Nº de combos concretos de cada clase (6, 4 o 12).
COMBO_COUNTS: List[int] = [len(h["combos"]) for h in HAND_CLASSES]
TOTAL_COMBOS = sum(COMBO_COUNTS)  # == 1326

# Peso = probabilidad de recibir cada clase con una mano uniformemente al azar.
HAND_WEIGHTS: List[float] = [c / TOTAL_COMBOS for c in COMBO_COUNTS]


def combos_of(index: int) -> List[Tuple[str, str]]:
    """Devuelve los combos concretos (pares de strings tipo 'As','Kd') de la clase."""
    return HAND_CLASSES[index]["combos"]


def _self_check() -> None:
    """Chequeos de consistencia; se ejecutan al correr el módulo directamente."""
    assert len(HAND_CLASSES) == N_HANDS, len(HAND_CLASSES)
    assert TOTAL_COMBOS == 1326, TOTAL_COMBOS
    assert len(set(LABELS)) == N_HANDS, "etiquetas duplicadas"
    assert abs(sum(HAND_WEIGHTS) - 1.0) < 1e-9
    n_pairs = sum(1 for h in HAND_CLASSES if h["kind"] == "pair")
    n_suited = sum(1 for h in HAND_CLASSES if h["kind"] == "suited")
    n_off = sum(1 for h in HAND_CLASSES if h["kind"] == "offsuit")
    assert (n_pairs, n_suited, n_off) == (13, 78, 78), (n_pairs, n_suited, n_off)
    print("hands.py OK:", N_HANDS, "clases,", TOTAL_COMBOS, "combos")
    print("  primeras:", LABELS[:5], "...")
    print("  ejemplo combos AA:", combos_of(LABEL_TO_INDEX["AA"]))


if __name__ == "__main__":
    _self_check()
