# =============================================================================
# Model : model_mic.mod
# =============================================================================

# --- DIMENSION PARAMETERS ---
param nT;            
param nB;            
param nbG;           
param nbD;         
param M;  

# --- BASIC SETS ---
set T = 1..nT;       
set V = 1..nB;       
set bG = 1..nbG;     
set bD = 1..nbD;     

set G;               
set D;               
set refB;            

set GB {V} default {};  
set DB {V} default {};  

# --- NETWORK AND LINES ---
param Bsusc {V,V} default 0; 
param smax {V,V} default 0;  
set LINES := {n in V, m in V: smax[n,m] > 0};

# --- HEURISTIC ---
set G_eligible within G default G; 

# --- TECHNICAL PARAMETERS ---
param pgmin {G};      
param pgmax {G};      
param ru {G};         
param rd {G};         
param pg0 {G};        
param u0 {G};         
param Gen_Bus {g in G} symbolic; 

# --- BIDS ---
param lbG {G, bG, T} default 0; 
param pbG {G, bG, T} default 0; 
param lbD {D, bD, T} default 0; 
param pbD {D, bD, T} default 0; 

# --- VARIABLES ---
var P_G {g in G, b in bG, t in T} >= 0; 
var P_D {d in D, b in bD, t in T} >= 0; 
var Theta {n in V, t in T}; 
var U {g in G, t in T} binary;

var Flow {n in V, m in V, t in T: (n,m) in LINES}; 

# Auxiliary Variables
var pg_total {g in G, t in T} = sum {b in bG} P_G[g,b,t];
var pd_total {d in D, t in T} = sum {b in bD} P_D[d,b,t];

# --- OBJECTIVE FUNCTION ---
maximize Social_Welfare:
    sum {t in T, d in D, b in bD} (lbD[d,b,t] * P_D[d,b,t]) -
    sum {t in T, g in G, b in bG} (lbG[g,b,t] * P_G[g,b,t]);

# --- CONSTRAINTS ---

# Offer limits
s.t. Limit_G {g in G, b in bG, t in T}:
    P_G[g,b,t] <= pbG[g,b,t];

s.t. Limit_D {d in D, b in bD, t in T}:
    P_D[d,b,t] <= pbD[d,b,t];

# Physical limits
s.t. Gen_Physical_Max {g in G, t in T}:
    pg_total[g,t] <= pgmax[g]*U[g, t];

s.t. Gen_Physical_Min {g in G, t in T}:
    pg_total[g,t] >= pgmin[g]*U[g, t];

# Ramps
s.t. Ramp_Up {g in G, t in T}:
    pg_total[g,t] - (if t=1 then pg0[g] else pg_total[g,t-1]) <= ru[g];

s.t. Ramp_Down {g in G, t in T}:
    (if t=1 then pg0[g] else pg_total[g,t-1]) - pg_total[g,t] <= rd[g];

# --- MPA CONSTRAINTS ---
s.t. System_Balance {t in T}:
    sum {g in G} pg_total[g,t] - sum {d in D} pd_total[d,t] = 0; 

# --- TCMPA CONSTRAINTS ---
s.t. DC_Flow_Eq {n in V, m in V, t in T: (n,m) in LINES}:
    Flow[n,m,t] = Bsusc[n,m] * (Theta[n,t] - Theta[m,t]);

s.t. Node_Balance {n in V, t in T}:
    sum {g in G: g in GB[n]} pg_total[g,t] - 
    sum {d in D: d in DB[n]} pd_total[d,t] 
    = 
    sum {m in V: (n,m) in LINES} Flow[n,m,t] - sum {m in V: (m,n) in LINES} Flow[m,n,t];

s.t. Line_Capacity_Max {n in V, m in V, t in T: (n,m) in LINES}:
    Flow[n,m,t] <= smax[n,m];

s.t. Line_Capacity_Min {n in V, m in V, t in T: (n,m) in LINES}:
    Flow[n,m,t] >= -smax[n,m];

s.t. Ref_Bus_Angle {r in refB, t in T}:
    Theta[r, t] = 0;

# --- HEURISTIC CONTRAINTS ---
s.t. Heuristic_Constraint {g in G, t in T: g not in G_eligible}:
    U[g,t] <= (if (t=1 and pg0[g] > 0) then 1 else 0);


# --- PROBLEM DEFINITION ---
problem MPA:
    P_G, P_D, U, pg_total, pd_total,
    Social_Welfare,
    Limit_G,
    Limit_D,
    Gen_Physical_Max,
    Gen_Physical_Min,
    Ramp_Up,
    Ramp_Down,
    System_Balance;

problem TCMPA:
    P_G, P_D, Theta, U, pg_total, pd_total, Flow,
    Social_Welfare,
    Limit_G,
    Limit_D,
    Gen_Physical_Max,
    Gen_Physical_Min,
    Ramp_Up,
    Ramp_Down,
    DC_Flow_Eq,
    Node_Balance,
    Line_Capacity_Max,
    Line_Capacity_Min,
    Ref_Bus_Angle;

problem MPA_Heuristic:
    P_G, P_D, U, pg_total, pd_total,
    Social_Welfare,
    Limit_G,
    Limit_D,
    Gen_Physical_Max,
    Gen_Physical_Min,
    Ramp_Up,
    Ramp_Down,
    System_Balance,
    Heuristic_Constraint;

problem TCMPA_Heuristic:
    P_G, P_D, Theta, U, pg_total, pd_total, Flow,
    Social_Welfare,
    Limit_G,
    Limit_D,
    Gen_Physical_Max,
    Gen_Physical_Min,
    Ramp_Up,
    Ramp_Down,
    DC_Flow_Eq,
    Node_Balance,
    Line_Capacity_Max,
    Line_Capacity_Min,
    Ref_Bus_Angle,
    Heuristic_Constraint;