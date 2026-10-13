"""Seed policy helper. See docs/seed_policy.md."""
import os
import random

import numpy as np


def set_seed(seed: int) -> None:
    """Seed every RNG the project uses. Call once at the top of each script."""
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


def rng(seed: int) -> np.random.Generator:
    """Use this for any new randomness (e.g. synthetic anomaly injection)."""
    return np.random.default_rng(seed)
