# E035 — Outcome-free advanced Feature Engineering

Segunda ola después de E031-E033.

Usa únicamente E030 train y tres folds temporales expansivos.

## Variantes

1. atomic
2. missingness_frequency
3. robust_bins
4. geo_inventory_relative
5. combined_v2

## Nuevas familias

- missingness count/pattern;
- train-only categorical frequency;
- train-only quantile bins;
- price/area relative to contemporaneous train inventory;
- preferred municipality/corridor centroid distance.

No usa target encoding ni test E030.

## CI

Governed by `.github/workflows/e035-advanced-fe.yml`.
