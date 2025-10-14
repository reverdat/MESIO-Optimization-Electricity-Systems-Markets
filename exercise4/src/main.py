
from pyomo.environ import SolverFactory, TerminationCondition, value

from models.singe_period_auction import model


if __name__ == "__main__":
    solver = SolverFactory('highs')

    instance_t1 = model.create_instance('exercise4/src/instances/data_t1.dat')
    results_t1 = solver.solve(instance_t1, tee=True)
    if results_t1.solver.termination_condition == TerminationCondition.optimal:
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
    
    instance_t2 = model.create_instance('exercise4/src/instances/data_t2.dat')
    results_t2 = solver.solve(instance_t2, tee=True)    
    if results_t2.solver.termination_condition == TerminationCondition.optimal:
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