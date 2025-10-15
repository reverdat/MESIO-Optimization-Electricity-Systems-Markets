
from pyomo.environ import SolverFactory, TerminationCondition, value

from models.single_period_auction import model as model_single_period
from models.multi_period_auction import model as model_multi_period

from plots import plot_single_period_auction, plot_multiperiod_auction

import matplotlib.pyplot as plt

if __name__ == "__main__":
    solver = SolverFactory('highs')

    instance_t1 = model_single_period.create_instance('exercise4/src/instances/data_t1.dat')
    results_t1 = solver.solve(instance_t1, tee=True)
    if results_t1.solver.termination_condition == TerminationCondition.optimal:
        fig1, ax1 = plot_single_period_auction(instance_t1)
        plt.savefig('exercise4/src/img/market_clearing_t1.png', dpi=300, bbox_inches='tight')
        plt.show()

        print("\n=== PERIOD t=1 RESULTS ===")
        print(f"Social Welfare: {value(instance_t1.obj)}")
        
        for i in instance_t1.G:
            total_gen = 0
            for k in instance_t1.B_G:
                p_val = value(instance_t1.P_G[i, k])
                total_gen += p_val
                print(f"  Block {k}: P_G={p_val} MW @ λ={value(instance_t1.Lambda_B_G[i, k])}")
            print(f"  Total Generation: {total_gen} MW")
        
        for d in instance_t1.D:
            print(f"\nDemand {d}:")
            total_dem = 0
            for k in instance_t1.B_D:
                p_val = value(instance_t1.P_D[d, k])
                total_dem += p_val
                print(f"  Block {k}: P_D={p_val} MW @ λ={value(instance_t1.Lambda_B_D[d, k])}")
            print(f"  Total Demand: {total_dem} MW")
    
    print("\n" + "="*50 + "\n")
    
    instance_t2 = model_single_period.create_instance('exercise4/src/instances/data_t2.dat')
    results_t2 = solver.solve(instance_t2, tee=True)    
    if results_t2.solver.termination_condition == TerminationCondition.optimal:
        fig1, ax1 = plot_single_period_auction(instance_t2)
        plt.savefig('exercise4/src/img/market_clearing_t2.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        print("\n=== PERIOD t=2 RESULTS ===")
        print(f"Social Welfare: {value(instance_t2.obj)}")
        
        for i in instance_t2.G:
            print(f"Generator {i} ===")
            total_gen = 0
            for k in instance_t2.B_G:
                p_val = value(instance_t2.P_G[i, k])
                total_gen += p_val
                print(f"  Block {k}: P_G={p_val} MW @ λ={value(instance_t2.Lambda_B_G[i, k])}")
            print(f"  Total Generation: {total_gen} MW")
        
        for d in instance_t2.D:
            print(f"\nDemand {d}:")
            total_dem = 0
            for k in instance_t2.B_D:
                p_val = value(instance_t2.P_D[d, k])
                total_dem += p_val
                print(f"  Block {k}: P_D={p_val} MW @ λ={value(instance_t2.Lambda_B_D[d, k])}")
            print(f"  Total Demand: {total_dem} MW")

    instance = model_multi_period.create_instance('exercise4/src/instances/data_all.dat')
    
    solver = SolverFactory('highs')
    results = solver.solve(instance, tee=True)
    
    if results.solver.termination_condition == TerminationCondition.optimal:
        fig2, axes2 = plot_multiperiod_auction(instance)
        plt.savefig('exercise4/src/img/multiperiod_auction.png', dpi=300, bbox_inches='tight')
        plt.show()

        print("\n" + "="*60)
        print("=== MULTI-PERIOD MARKET CLEARING RESULTS ===")
        print("="*60)
        print(f"\nTotal Social Welfare: ${value(instance.obj):.2f}")
        
        for t in instance.T:
            print("\n" + "-"*60)
            print(f"PERIOD t={t}")
            print("-"*60)
            
            total_gen_period = 0
            total_dem_period = 0
            
            for i in instance.G:
                print(f"\nGenerator {i}:")
                print(f"  Status: u={value(instance.u[i, t])}")
                print(f"  Total Generation: P^T_G = {value(instance.P_G_total[i, t]):.2f} MW")
                for k in instance.B_G:
                    p_val = value(instance.P_G[i, t, k])
                    lambda_val = value(instance.Lambda_B_G[i, t, k])
                    print(f"    Block {k}: P_G={p_val:.2f} MW @ λ={lambda_val:.2f} $/MWh")
                total_gen_period += value(instance.P_G_total[i, t])
            
            for d in instance.D:
                print(f"\nDemand {d}:")
                print(f"  Total Demand: P^T_D = {value(instance.P_D_total[d, t]):.2f} MW")
                for k in instance.B_D:
                    p_val = value(instance.P_D[d, t, k])
                    lambda_val = value(instance.Lambda_B_D[d, t, k])
                    print(f"    Block {k}: P_D={p_val:.2f} MW @ λ={lambda_val:.2f} $/MWh")
                total_dem_period += value(instance.P_D_total[d, t])
            
            print(f"\n  Period Summary:")
            print(f"    Total Generation: {total_gen_period:.2f} MW")
            print(f"    Total Demand: {total_dem_period:.2f} MW")
            print(f"    Balance: {abs(total_gen_period - total_dem_period):.6f} MW")
        
        # Show ramp rates between periods
        print("\n" + "="*60)
        print("=== RAMP RATES ===")
        print("="*60)
        for i in instance.G:
            print(f"\nGenerator {i}:")
            for t in instance.T:
                if t == instance.T.first():
                    ramp = value(instance.P_G_total[i, t]) - value(instance.P_0[i])
                    print(f"  t={t}: Ramp from P_0 = {ramp:+.2f} MW (P_0={value(instance.P_0[i]):.2f} → {value(instance.P_G_total[i, t]):.2f})")
                else:
                    t_prev = instance.T.prev(t)
                    ramp = value(instance.P_G_total[i, t]) - value(instance.P_G_total[i, t_prev])
                    print(f"  t={t}: Ramp from t={t_prev} = {ramp:+.2f} MW ({value(instance.P_G_total[i, t_prev]):.2f} → {value(instance.P_G_total[i, t]):.2f})")
    else:
        print("\nSolver did not find an optimal solution")
        print(f"Termination condition: {results.solver.termination_condition}")