"""
This module contains the
    Stochastic Demand Economic Dispatch (SDED) with Mean-Variance as Risk Measure
Pyomo model formulation as an
AbstractModel.
"""

from pyomo.environ import (
    Var,
    Param,
    NonNegativeReals,
    RangeSet,
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
    Integers,
    Binary,
    summation,
)

model = AbstractModel(
    name="Stochastic Demand Economic Dispatch (SDED) with Mean-Variance as Risk Measure"
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
model.beta = Param()

model.pi = Param(model.S)  # Total system load (MW)
model.pd0 = Param(model.S)  # Total system load (MW)
model.la_c = Param(model.S)  # Curtailment penalization (EUR/MW)
model.la_s = Param(model.S)  # Surplus penalization (EUR/MW)


# Variables
model.P_G = Var(model.G, domain=NonNegativeReals)
model.P_S_minus = Var(model.S, domain=NonNegativeReals)
model.P_S_plus = Var(model.S, domain=NonNegativeReals)

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
    rule=lambda m: sum(
        m.pi[s]
        * ((m.la_c[s] * m.P_S_minus[s] + m.la_s[s] * m.P_S_plus[s]) - m.term2_expr) ** 2
        for s in m.S
    )
)


def Mean_Variance_Economic_Dispatch(model):
    return (
        model.term1_expr
        + (1 - model.beta) * model.term2_expr
        + model.beta * model.term3_expr
    )


model.obj = Objective(rule=Mean_Variance_Economic_Dispatch, sense=minimize)


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
