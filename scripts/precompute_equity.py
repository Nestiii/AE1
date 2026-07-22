#!/usr/bin/env python3
"""
Genera (y cachea) la matriz 169x169 de equity all-in preflop.

Uso:
    python scripts/precompute_equity.py [--samples N] [--seed S] [--out PATH]

Requiere `eval7`. Solo hace falta correrlo para REGENERAR la matriz: el resto
del proyecto usa el archivo ya versionado en data/equity_169x169.npy.
"""

import argparse
import os
import sys
import time

# Permite ejecutar el script sin instalar el paquete (agrega src/ al path).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from pushfold.equity import DEFAULT_CACHE, compute_equity_matrix, save_equity_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=4000,
                        help="repartos Monte Carlo por matchup (default 4000)")
    parser.add_argument("--seed", type=int, default=42, help="semilla (default 42)")
    parser.add_argument("--out", type=str, default=DEFAULT_CACHE,
                        help="ruta de salida .npy")
    args = parser.parse_args()

    print(f"Calculando matriz de equity: samples={args.samples}, seed={args.seed}")
    t0 = time.time()
    matrix = compute_equity_matrix(n_samples=args.samples, seed=args.seed)
    print(f"Listo en {time.time() - t0:.1f} s")
    save_equity_matrix(matrix, args.out)


if __name__ == "__main__":
    main()
