"""
This module contains the
    Stochastic Demand Economic Dispatch (SDED) with CVaR as Risk Measure
Pyomo model formulation as an
AbstractModel.
"""

from pyomo.environ import (
    Var,
    Param,
    NonNegativeReals,
    Reals,
    Expression,
    Objective,
    AbstractModel,
    maximize,
    minimize,
    Set,
    Constraint,
    SolverFactory,
    TerminationCondition,
    value,
    summation,
)

model = AbstractModel(
    name="Stochastic Demand Economic Dispatch (SDED) with CVaR as Risk Measure"
)


# Sets
model.G = Set()  # Set of generators
model.S = Set()  # Set of stochastic scenarios

# Parameters
model.cq = Param(model.G)
model.cl = Param(model.G)
model.cb = Param(model.G)
model.pgmin = Param(model.G)
model.pgmax = Param(model.G)

# Risk Parameters
model.beta = Param()
model.alpha = Param(default=0.95)

model.pi = Param(model.S)  # Probability of scenario
model.pd0 = Param(model.S)  # Total system load (MW)
model.la_c = Param(model.S)  # Curtailment penalization (EUR/MW)
model.la_s = Param(model.S)  # Surplus penalization (EUR/MW)


# Variables
model.P_G = Var(model.G, domain=NonNegativeReals)
model.P_S_minus = Var(model.S, domain=NonNegativeReals)
model.P_S_plus = Var(model.S, domain=NonNegativeReals)

# CVaR Auxiliary Variables
model.VaR = Var(domain=Reals)
model.Tail_Loss = Var(model.S, domain=NonNegativeReals)


# Expressions
model.term1_expr = Expression(
    rule=lambda m: sum(
        m.cq[g] * (m.P_G[g] ** 2) + m.cl[g] * m.P_G[g] + m.cb[g] for g in m.G
    )
)

model.term2_expr = Expression(
    rule=lambda m: sum(
        m.pi[s] * (m.la_c[s] * m.P_S_minus[s] + m.la_s[s] * m.P_S_plus[s]) for s in m.S
    )
)


model.term3_expr = Expression(
    rule=lambda m: m.VaR
    + (1.0 / (1.0 - m.alpha)) * sum(m.pi[s] * m.Tail_Loss[s] for s in m.S)
)


def CVaR_Economic_Dispatch(model):
    return (
        model.term1_expr
        + (1 - model.beta) * model.term2_expr
        + model.beta * model.term3_expr
    )


model.obj = Objective(rule=CVaR_Economic_Dispatch, sense=minimize)


# Constraints
def Matched_Demand(model, s):
    return (
        sum(model.P_G[g] for g in model.G) + model.P_S_minus[s] - model.P_S_plus[s]
        == model.pd0[s]
    )


model.Power_Balance = Constraint(model.S, rule=Matched_Demand)


def Minimum_Power_Constraint(model, g):
    return model.P_G[g] >= model.pgmin[g]


def Maximum_Power_Constraint(model, g):
    return model.P_G[g] <= model.pgmax[g]


model.Min_Power = Constraint(model.G, rule=Minimum_Power_Constraint)
model.Max_Power = Constraint(model.G, rule=Maximum_Power_Constraint)


def CVaR_Tail_Constraint(model, s):
    imbalance_cost_s = model.la_c[s] * model.P_S_minus[s] + model.la_s[s] * model.P_S_plus[s]
    return model.Tail_Loss[s] >= imbalance_cost_s - model.VaR


model.CVaR_Def = Constraint(model.S, rule=CVaR_Tail_Constraint)