import numpy as np
import pandas as pd

from pyomo.environ import SolverFactory, TerminationCondition, value

from instances.generate import generate_instance
from models.sded_mean_variance import model as mean_variance_model
from models.sded_cvar import model as cvar_model
from plots import plot_efficient_frontiers



def main():
    main_seed = 1234
    rng = np.random.default_rng(seed=main_seed)

    solver = SolverFactory("highs")

    n_scenarios = 100
    sigma = 0.05
    alpha_cvar = 0.05

    beta_values = np.arange(0, 1.01, 0.01)

    results = []

    models_config = {
        "Mean-Variance": {"abstract": mean_variance_model, "alpha": None},
        "CVaR": {"abstract": cvar_model, "alpha": alpha_cvar},
    }

    print(
        f"{'Model':<15} | {'Beta':<5} | {'Obj':<10} | {'Gen Cost':<10} | {'Risk (Obj)':<10} | {'Avg Demand':<10}"
    )
    print("-" * 85)

    for model_name, config in models_config.items():
        for beta in beta_values:
            inst = generate_instance(
                abstract_model=config["abstract"],
                n_scenarios=n_scenarios,
                sigma=sigma,
                beta=beta,
                alpha=config["alpha"],
                rng=rng,
            )

            sol = solver.solve(inst)

            if sol.solver.termination_condition == TerminationCondition.optimal:
                val_obj = value(inst.obj)
                val_term1 = value(inst.term1_expr)
                val_term2 = value(inst.term2_expr)
                val_term3 = value(inst.term3_expr)

                avg_demand = sum(inst.pd0[s] for s in inst.S) / n_scenarios

                print(
                    f"{model_name:<15} | {beta:.2f}  | {val_obj:.2f}     | {val_term1:.2f}     | {val_term3:.2f}       | {avg_demand:.2f}"
                )

                results.append(
                    {
                        "Model": model_name,
                        "Beta": beta,
                        "Objective": val_obj,
                        "Generation_Cost": val_term1,
                        "Expected_Imbalance": val_term2,
                        "Risk_Measure": val_term3,
                        "Total_Expected_Cost": val_term1 + val_term2,
                        "Average_Scenario_Demand": avg_demand,
                    }
                )
            else:
                print(f"Warning: {model_name} (Beta {beta}) infeasible or failed.")

    return pd.DataFrame(results)


if __name__ == "__main__":
    df = main()
    plot_efficient_frontiers(df)
