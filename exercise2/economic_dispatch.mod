set T; 

# Parameters 
param S{T} >= 0;  
param D{T} >= 0; 

param E >= 0;  
param Pmax >= 0;  
param rho >= 0, <= 1;  
param SOC_min >= 0, <= 1;  
param SOC_max >= 0, <= 1;  
param SOC0 >= 0, <= 1;  
param SOCT >= 0, <= 1;  

param C_s >= 0;  
param C_e >= 0;  

# Decision Variables
var s{T} >= 0;  
var x{T} >= 0;  
var y{T} >= 0;  

# Objective Function
minimize Total_Cost:
    sum{t in T} (C_s * s[t] + C_e * (x[t] + y[t]));

# Constraints

# Solar generation cannot exceed available solar power
subject to Solar_Limit{t in T}:
    s[t] + x[t] <= S[t];

# Demand must be met exactly
subject to Demand_Balance{t in T}:
    s[t] + y[t] = D[t];

# State of charge bounds
subject to SOC_Lower{t in T}:
    SOC0 * E + sum{tp in T: tp <= t} (rho * x[tp] - (1/rho) * y[tp]) >= SOC_min * E;

subject to SOC_Upper{t in T}:
    SOC0 * E + sum{tp in T: tp <= t} (rho * x[tp] - (1/rho) * y[tp]) <= SOC_max * E;


# Maximum charge and discharge power rate constraints
subject to Charge_Rate{t in T}:
    rho * x[t] <= Pmax;

subject to Discharge_Rate{t in T}:
    (1/rho) * y[t] <= Pmax;

# Final state of charge constraint
subject to Final_SOC:
    SOC0 * E + sum{t in T} (rho * x[t] - (1/rho) * y[t]) = SOCT * E;