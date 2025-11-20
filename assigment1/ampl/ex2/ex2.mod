# ex2.mod - DC-OPF with Generalized Unit Commitment

set V;                     # nodal buses
set G;                     # thermal generators 
set T := 1..24;            # time periods 
set L within {V,V};        # set of directed lines (n,m) 
set D; 					   # demands
set D_n{V} within D; 	   # Demands connected to each node
set G_n{V} within G; 	   # Generators connected to each node


param Cq{G} >= 0;                  # quadratic cost coef
param Cl{G} >= 0;                  # linear cost coef
param Cb{G} >= 0;                  # fixed cost coef
param Csud{G} >= 0;                # startup/shutdown cost
param Pgmin{G} >= 0;
param Pgmax{G} >= 0;
param Ru{G} >= 0;                  # ramp up limit (per hour)
param Rd{G} >= 0;                  # ramp down limit
param Pg0{G} default 0;            # generation at time 0
param U0{G} integer default 0;     # on/off state at time 0

param TU{G} >= 0 default 4;        # minimum uptime
param TD{G} >= 0 default 5;        # minimum downtime
param TUini{G} >= 0 default 0;     # remaining uptime at t=0
param TDini{G} >= 0 default 0;     # remaining downtime at t=0

param Bsusc{L} > 0;                # susceptance (B_{n,m})
param smax{L} >= 0;                # thermal limit of line (absolute)

# Demand: Pd[n,t]
param Pd{D, T} >= 0 default 0;

# Reference bus
param refB integer;

# Variables
var p{g in G, t in T} >= 0;        # power generation
var u{g in G, t in T} binary;      # on/off status of generator
var vsu{g in G, t in T} >= 0;      # startup/shutdown cost variable
var theta{n in V, t in T};         # voltage angle (real)
var f{(i,j) in L, t in T};         # flow on directed line (i,j)

# Objective:
minimize TotalCost:
    sum{t in T, i in G} ( Cq[i] * p[i,t]^2 + Cl[i] * p[i,t] + Cb[i] * u[i,t] + vsu[i,t] );

# Constraints

# generation limits and unit commitment
s.t. GenMin{i in G, t in T}:
    Pgmin[i]*u[i,t] <= p[i,t];
    
s.t. GenMax{i in G, t in T}:    
    p[i,t] <= Pgmax[i]*u[i,t];

# DC flow definition for each directed line (i,j)
s.t. DCFlow{(i,j) in L, t in T}:
    f[i,j,t] = Bsusc[i,j] * ( theta[i,t] - theta[j,t] );

# line capacity
s.t. LineCap{(i,j) in L, t in T}:
    - smax[i,j] <= f[i,j,t] <= smax[i,j];

# nodal balance
s.t. NodalBalance{n in V, t in T}:
    sum{g in G_n[n]} p[g,t]
    = sum{d in D_n[n]} Pd[d,t]
      + ( sum{(n,m) in L} f[n,m,t] - sum{(m,n) in L} f[m,n,t] );

# reference angle
s.t. RefAngle{t in T}:
    theta[refB,t] = 0;

# ramping constraints between period 0 and 1
s.t. RampInitUp{g in G}:
    p[g,1] - Pg0[g] <= Ru[g];
s.t. RampInitDown{g in G}:
    Pg0[g] - p[g,1] <= Rd[g];

# ramping constraints between consecutive periods
s.t. RampUp{g in G, t in T: t > 1}:
    p[g,t] - p[g,t-1] <= Ru[g];
s.t. RampDown{g in G, t in T: t > 1}:
    p[g,t-1] - p[g,t] <= Rd[g]; 

# startup/shutdown cost
# For first period
s.t. SU_def_init{g in G}:
    vsu[g,1] >= Csud[g] * (u[g,1] - U0[g]);
s.t. SD_def_init{g in G}:
    vsu[g,1] >= Csud[g] * (U0[g] - u[g,1]);

# For subsequent periods
s.t. SU_SD_def{g in G, t in T: t > 1}:
    vsu[g,t] >= Csud[g] * (u[g,t] - u[g,t-1]);
s.t. SD_def{g in G, t in T: t > 1}:
    vsu[g,t] >= Csud[g] * (u[g,t-1] - u[g,t]);



# Minimum uptime
s.t. MinUptime{g in G, t in T: t > 1 and TU[g] > 0}: # if generator starts up at time t, it must stay on for TU periods
    sum{tp in t..min(t+TU[g]-1, card(T))} u[g,tp] >= TU[g] * (u[g,t] - u[g,t-1]);
s.t. MinUptimeInit{g in G: TU[g] > 0}: # startup at t=1
    sum{tp in 1..min(TU[g], card(T))} u[g,tp] >= TU[g] * (u[g,1] - U0[g]);
s.t. InitialUptime{g in G: TUini[g] > 0}: #  if generator was on at t=0 and needs to stay on
    sum{tp in 1..min(TUini[g], card(T))} u[g,tp] >= TUini[g];

# Minimum downtime:
s.t. MinDowntime{g in G, t in T: t > 1 and TD[g] > 0}: # if generator shuts down at time t, it must stay off for TD periods
    sum{tp in t..min(t+TD[g]-1, card(T))} (1 - u[g,tp]) >= TD[g] * (u[g,t-1] - u[g,t]);
s.t. MinDowntimeInit{g in G: TD[g] > 0}: # startup at t=1
    sum{tp in 1..min(TD[g], card(T))} (1 - u[g,tp]) >= TD[g] * (U0[g] - u[g,1]);
s.t. InitialDowntime{g in G: TDini[g] > 0}:  #  if generator was on at t=0 and needs to stay on
    sum{tp in 1..min(TDini[g], card(T))} (1 - u[g,tp]) >= TDini[g];

## Problem definition
problem DC_OPF_GUC_No_Initial:
    p, u, vsu, theta, f,
    TotalCost,
    GenMin,
    GenMax,
    DCFlow,
    LineCap,
    NodalBalance,
    RefAngle,
    RampInitUp,
    RampInitDown,
    RampUp,
    RampDown,
    SU_def_init,
    SD_def_init,
    SU_SD_def,
    SD_def,
    MinUptime,
    MinUptimeInit,
    MinDowntime,
    MinDowntimeInit;

problem DC_OPF_GUC_Initial_Only:
    p, u, vsu, theta, f,
    TotalCost,
    GenMin,
    GenMax,
    DCFlow,
    LineCap,
    NodalBalance,
    RefAngle,
    RampInitUp,
    RampInitDown,
    RampUp,
    RampDown,
    SU_def_init,
    SD_def_init,
    SU_SD_def,
    SD_def,
    InitialUptime,
    InitialDowntime;