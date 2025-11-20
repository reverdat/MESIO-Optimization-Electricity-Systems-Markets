# 1a.mod - DC-OPF with unit commitment

set V;                     # nodal buses
set G;                     # thermal generators (names)
set T := 1..24;            # time periods 
set L within {V,V};        # set of directed lines (n,m)
set D; 					   # demands
set D_n{V} within D; 	   # Demands connected to each node
set G_n{V} within G; 	   # Generators connected to eahc node


param Cq{G} >= 0;                  # quadratic cost coef
param Cl{G} >= 0;                  # linear cost coef
param Cb{G} >= 0;                  # fixed cost coef (often cost*u)
param Csud{G} >= 0;                # startup/shutdown cost coefficient
param Pgmin{G} >= 0;
param Pgmax{G} >= 0;
param Ru{G} >= 0;                  # ramp up limit (per hour)
param Rd{G} >= 0;                  # ramp down limit
param Pg0{G} default 0;            # generation at time 0
param U0{G} integer default 0;     # on/off state at time 0

param Bsusc{L} > 0;                    # susceptance (B_{n,m})
param smax{L} >= 0;                # thermal limit of line (absolute)

# Demand: Pd[n,t] 
param Pd{D, T} >= 0 default 0;

# Reference bus
param refB integer;

# Variables
var p{g in G, t in T} >= 0;          # power generation
var u{g in G, t in T} binary;        # on/off status of generator
var vsu{g in G, t in T} >= 0;       # startup/shutdown cost variable (non-negative)
var theta{n in V, t in T};         # voltage angle (real)
var f{(i,j) in L, t in T};         # flow on directed line (i,j)

# Objective: sum over time and generators cost (quadratic)
minimize TotalCost:
    sum{t in T, i in G} ( Cq[i] * p[i,t]^2 + Cl[i] * p[i,t] + Cb[i] * u[i,t] + vsu[i,t] );

# Constraints

# generation limits and unit commitment coupling
s.t. GenMin{i in G, t in T}:
    Pgmin[i]*u[i,t] <= p[i,t];
    
s.t. GenMax{i in G, t in T}:    
    p[i,t] <= Pgmax[i]*u[i,t];

# DC flow definition for each directed line (i,j)
s.t. DCFlow{(i,j) in L, t in T}:
    f[i,j,t] = Bsusc[i,j] * ( theta[i,t] - theta[j,t] );

# line capacity (flow may be positive or negative but we store both directions as separate entries
# if you only provide one direction in L, the bounds are symmetric here)
s.t. LineCap{(i,j) in L, t in T}:
    - smax[i,j] <= f[i,j,t] <= smax[i,j];

# nodal balance: sum of generation at node = demand + net outgoing flows
# we treat L as directed list of provided pairs;
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

s.t. RampUp{g in G, t in T: t > 1}:
    p[g,t] - p[g,t-1] <= Ru[g];
s.t. RampDown{g in G, t in T: t > 1}:
    p[g,t-1] - p[g,t] <= Rd[g]; 


# startup/shutdown cost linearization constraints
# For first period
s.t. SU_def_init{g in G}:
    vsu[g,1] >= Csud[g] * (u[g,1] - U0[g]);
s.t. SD_def_init{g in G}:
    vsu[g,1] >= Csud[g] * (U0[g] - u[g,1]);

# For subsequent periods
s.t. SU_SD_def{g in G, t in 2..24}:
    vsu[g,t] >= Csud[g] * (u[g,t] - u[g,t-1]);
s.t. SD_def{g in G, t in 2..24}:
    vsu[g,t] >= Csud[g] * (u[g,t-1] - u[g,t]);

# optional: link initial status for p when u0=0 to avoid p>0 (already enforced by GenMinMax with Pg0 and U0)
# variable domains are set above

# End of model.mod