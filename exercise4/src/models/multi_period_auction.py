from pyomo.environ import (
    ConcreteModel,
    Model,
    Var,
    Param,
    NonNegativeReals,
    RangeSet,
    Objective,
    AbstractModel,
    maximize,
    Set,
    Constraint,
    SolverFactory,
    TerminationCondition,
    value,
    Integers,
    Binary,
    summation,
)

model = AbstractModel(name="Multi-Period Market Clearing Model")

# Sets
model.T = Set(within=Integers, ordered=True)
model.G = Set(within=Integers)
model.D = Set(within=Integers)  
model.B_G = Set(within=Integers) 
model.B_D = Set(within=Integers)  

# Parameters
model.P_max = Param(model.G)
model.P_min = Param(model.G)
model.R_up = Param(model.G)
model.R_dn = Param(model.G)
model.P_0 = Param(model.G)
model.U_0 = Param(model.G)
model.M = Param(default=100000)


model.P_B_G = Param(model.G, model.T, model.B_G)
model.Lambda_B_G = Param(model.G, model.T, model.B_G)

model.P_B_D = Param(model.D, model.T, model.B_D)
model.Lambda_B_D = Param(model.D, model.T, model.B_D)

model.delta_t = Param(default=1.0)

# Variables
model.P_G = Var(
    model.G, model.T, model.B_G, domain=NonNegativeReals
)  
model.P_D = Var(
    model.D, model.T, model.B_D, domain=NonNegativeReals
)  
model.P_G_total = Var(
    model.G, model.T, domain=NonNegativeReals
)  
model.P_D_total = Var(model.D, model.T, domain=NonNegativeReals)  
model.u = Var(model.G, model.T, domain=Binary)  

# Objective function - Maximize Social Welfare
def Social_Welfare(model):
    term1 = sum(
        model.Lambda_B_D[d, t, k] * model.P_D[d, t, k] * model.delta_t
        for d in model.D
        for t in model.T
        for k in model.B_D
    )

    term2 = sum(
        model.Lambda_B_G[i, t, k] * model.P_G[i, t, k] * model.delta_t
        for i in model.G
        for t in model.T
        for k in model.B_G
    )

    return term1 - term2


model.obj = Objective(rule=Social_Welfare, sense=maximize)

# Constraints
def Matched_Generation(model, i, t, k):
    return model.P_G[i, t, k] <= model.P_B_G[i, t, k]


def Matched_Demand(model, d, t, k):
    return model.P_D[d, t, k] <= model.P_B_D[d, t, k]


def Total_Generation(model, i, t):
    return model.P_G_total[i, t] == sum(model.P_G[i, t, k] for k in model.B_G)


def Total_Demand(model, d, t):
    return model.P_D_total[d, t] == sum(model.P_D[d, t, k] for k in model.B_D)


def Market_Equilibrium(model, t):
    return sum(model.P_D_total[d, t] for d in model.D) == sum(
        model.P_G_total[i, t] for i in model.G
    )


def Ramp_Up_Limit(model, i, t):
    if t == model.T.first():
        return model.P_G_total[i, t] - model.P_0[i] <= model.R_up[i]
    else:
        t_prev = model.T.prev(t)
        return model.P_G_total[i, t] - model.P_G_total[i, t_prev] <= model.R_up[i]


def Ramp_Down_Limit(model, i, t):
    if t == model.T.first():
        return model.P_G_total[i, t] - model.P_0[i] >= -model.R_dn[i]
    else:
        t_prev = model.T.prev(t)
        return model.P_G_total[i, t] - model.P_G_total[i, t_prev] >= -model.R_dn[i]


def Generation_Min_Limit(model, i, t):
    return model.P_G_total[i, t] >= 0


def Generation_Max_Limit(model, i, t):
    return model.P_G_total[i, t] <= model.M * model.u[i, t]


model.matched_gen = Constraint(model.G, model.T, model.B_G, rule=Matched_Generation)
model.matched_dem = Constraint(model.D, model.T, model.B_D, rule=Matched_Demand)
model.total_gen = Constraint(model.G, model.T, rule=Total_Generation)
model.total_dem = Constraint(model.D, model.T, rule=Total_Demand)
model.market_eq = Constraint(model.T, rule=Market_Equilibrium)
model.ramp_up = Constraint(model.G, model.T, rule=Ramp_Up_Limit)
model.ramp_down = Constraint(model.G, model.T, rule=Ramp_Down_Limit)
model.gen_min = Constraint(model.G, model.T, rule=Generation_Min_Limit)
model.gen_max = Constraint(model.G, model.T, rule=Generation_Max_Limit)
