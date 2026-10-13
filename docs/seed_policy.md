# Seed policy

1. **One base seed per run, read from `config.yaml` (`seed: 42`).** Nobody hardcodes a seed in code.
2. **Every script calls `src.seeds.set_seed(cfg["seed"])` first.** It seeds Python, NumPy, `PYTHONHASHSEED` and (if installed) PyTorch with deterministic cuDNN.
3. **New randomness uses a local generator:** `rng = src.seeds.rng(seed)`, passed explicitly. No global `np.random.*` calls in new code.
4. **Multi-seed experiments use the fixed list `[0, 1, 2, 3, 4]`**, decided now, before any results. Report mean ± std over all five. Never drop a seed after seeing its result.
5. **Synthetic anomaly injection uses its own seed (`seed + 1000`)**, so changing model seeds never changes the injected test set.
6. **Log the seed with every result** (spreadsheet row / MLflow run).
7. GARCH MLE in `arch` is deterministic given the data, so seeds matter from Phase 3 on; set them anyway so the habit is in place.
