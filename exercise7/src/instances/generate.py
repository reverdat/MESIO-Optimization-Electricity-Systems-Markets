"""
This module contains a function
which generates a simulation for
the stochastic demand and hence
create an instance for our problem
"""
from typing import Optional

import numpy as np
from scipy.stats import norm

from pyomo.environ import AbstractModel, ConcreteModel


class NormalDistribution:
    """
    A Normal-distributed random variables of parameters
        - mu: Mean value of the distribution
        - sigma: Standard deviation of the dsitribution
    """

    def __init__(
        self,
        mu: float,
        sigma: float,
        rng: np.random.Generator = None,
        seed: int = None,
    ):
        if rng is not None:
            self.rng = rng
        elif seed is not None:
            self.rng = np.random.default_rng(seed)
        else:
            self.rng = np.random.default_rng()

        self.mu = mu
        self.sigma = sigma
        self.params = {"mu": mu, "sigma": sigma}
        self.rv = norm

    def sample(self, n: int) -> np.array:
        return self.rv.rvs(loc=self.mu, scale=self.sigma, size=n, random_state=self.rng)


def generate_instance(
    abstract_model: AbstractModel,
    n_scenarios: int,
    sigma: float,
    beta: float,
    alpha: Optional[float],
    rng: np.random.Generator,
) -> ConcreteModel:
    scenario_set = [f"S{i}" for i in range(1, n_scenarios + 1)]
    data = {
        None: {
            # Sets
            "G": {None: ["G1", "G2", "G3"]},
            "S": {None: scenario_set},
            # Generation unit parameters
            "cq": {"G1": 0.0006, "G2": 0.0005, "G3": 0.0007},
            "cl": {"G1": 0.5, "G2": 0.6, "G3": 0.4},
            "cb": {"G1": 6, "G2": 5, "G3": 3},
            "pgmin": {"G1": 100, "G2": 100, "G3": 100},
            "pgmax": {"G1": 250, "G2": 250, "G3": 350},
        }
    }

    normal_sample = NormalDistribution(mu=1, sigma=sigma, rng=rng).sample(n_scenarios)

    def _positive_cutoff(arr: np.array):
        return np.maximum(arr, 0)

    data[None]["pi"] = dict(zip(scenario_set, [1/float(n_scenarios) for _ in range(n_scenarios)]))
    data[None]["beta"] = {None: beta}
    data[None]["pd0"] = dict(
        zip(
            scenario_set,
            [_ for _ in list(_positive_cutoff(800 * normal_sample))],
        )
    )
    data[None]["la_c"] = dict(
        zip(
            scenario_set,
            [_ for _ in list(_positive_cutoff(1.5 * normal_sample))],
        )
    )
    data[None]["la_s"] = dict(
        zip(
            scenario_set,
            [_ for _ in list(_positive_cutoff(1.0 * normal_sample))],
        )
    )
    
    if alpha is not None:
        data[None]["alpha"] = {None: alpha}

    return abstract_model.create_instance(data=data)
