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

model = AbstractModel(name="Single-Period Market Clearing Model (Simplified)")

# Sets
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

model.P_B_G = Param(model.G, model.B_G)
model.Lambda_B_G = Param(model.G, model.B_G)

model.P_B_D = Param(model.D, model.B_D)
model.Lambda_B_D = Param(model.D, model.B_D)

# Variables
model.P_G = Var(model.G, model.B_G, domain=NonNegativeReals)
model.P_D = Var(model.D, model.B_D, domain=NonNegativeReals)
#model.u = Var(model.G, domain=Binary)

# Objective function - Social Welfare
def Social_Welfare_Rule(model):
    term1 = sum(
        model.Lambda_B_D[d, k] * model.P_D[d, k] 
        for d in model.D for k in model.B_D
    )
    
    term2 = sum(
        model.Lambda_B_G[i, k] * model.P_G[i, k] 
        for i in model.G for k in model.B_G
    )
    
    return term1 - term2

model.obj = Objective(rule=Social_Welfare_Rule, sense=maximize)

# Constraints
def Matched_Generation(model, i, k):
    return model.P_G[i, k] <= model.P_B_G[i, k]
    
def Matched_Demand(model, d, k):
    return model.P_D[d, k] <= model.P_B_D[d, k]

def Market_Equilibrium(model):
    term1 = sum(model.P_D[d, k] for d in model.D for k in model.B_D)
    term2 = sum(model.P_G[i, k] for i in model.G for k in model.B_G)
    return term1 == term2

def Ramp_Up_Limit(model, i):
    term = sum(model.P_G[i, k] for k in model.B_G) - model.P_0[i]
    return term <= model.R_up[i]

def Ramp_Down_Limit(model, i):
    term = sum(model.P_G[i, k] for k in model.B_G) - model.P_0[i]
    return term >= -model.R_dn[i]

def Generation_Min_Limit(model, i):
    term = sum(model.P_G[i, k] for k in model.B_G)
    return term >= model.P_min[i] #* model.u[i]

def Generation_Max_Limit(model, i):
    term = sum(model.P_G[i, k] for k in model.B_G)
    return term <= model.P_max[i] #* model.u[i]

model.matched_gen = Constraint(model.G, model.B_G, rule=Matched_Generation)
model.matched_dem = Constraint(model.D, model.B_D, rule=Matched_Demand)
model.market_eq = Constraint(rule=Market_Equilibrium)
#model.ramp_up = Constraint(model.G, rule=Ramp_Up_Limit)
#model.ramp_down = Constraint(model.G, rule=Ramp_Down_Limit)
#model.gen_min = Constraint(model.G, rule=Generation_Min_Limit)
#model.gen_max = Constraint(model.G, rule=Generation_Max_Limit)