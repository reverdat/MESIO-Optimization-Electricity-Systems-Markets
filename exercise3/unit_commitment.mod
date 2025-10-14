set T; 
set G;

param C_q{G} >= 0;
param C_l{G} >= 0;
param C_b{G} >= 0;
param C_SU{G} >= 0;

param P_min{G} >= 0;
param P_max{G} >= 0;

param R{G} >= 0;
param P_0{G} >= 0;
param U_0{G} >= 0;

param D{T} >= 0;

var u{G, T} binary;
var p{G, T};
var v_SU{G, T} >= 0;


minimize Total_Cost:
    sum{t in T} sum{g in G} (C_q[g]*p[g, t]^2 + C_l[g]*p[g, t] + C_b[g]*u[g, t]) + sum{t in T} (sum{g in G} v_SU[g, t]);

subject to Demand_Satisfaction {t in T}:
    sum{g in G} p[g, t] == D[t]
;

subject to Capacity_Constraints {g in G, t in T}:
    (u[g, t]*P_min[g] <= p[g, t]) and (p[g, t] <= u[g, t]*P_max[g])
;

subject to Generator_Ramps_Initial {g in G}:
    ((-1)*R[g] <= p[g, 1] - P_0[g])  and (p[g, 1] - P_0[g] <= R[g])
;

subject to Generator_Ramps {g in G, t in T: t > 1}:
    ((-1)*R[g] <= p[g, t] - p[g, t-1]) and (p[g, t] - p[g, t-1] <= R[g])
;

subject to Startup_Cost_Initial {g in G}:
    v_SU[g, 1] >= C_SU[g]*(u[g, 1] - U_0[g])
;


subject to Startup_Cost {g in G, t in T: t > 1}:
    v_SU[g, t] >= C_SU[g]*(u[g, t] - u[g, t-1])
;

subject to Shutdown_Cost_Initial {g in G}:
    v_SU[g, 1] >= C_SU[g]*(U_0[g] - u[g, 1])
; 


subject to Shutdown_Cost {g in G, t in T: t > 1}:
    v_SU[g, t] >= C_SU[g]*(u[g, t-1] - u[g, t])
;
