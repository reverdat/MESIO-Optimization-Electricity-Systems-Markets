import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

def plot_efficient_frontiers(df_results):
    sns.set_style("whitegrid")
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
    
    models = ["Mean-Variance", "CVaR"]
    
    for i, model_name in enumerate(models):
        ax = axes[i]
        
        data = df_results[df_results["Model"] == model_name].copy()
        
        if data.empty:
            ax.text(0.5, 0.5, "No Data", ha='center')
            continue
   
        sc = ax.scatter(
            data["Risk_Measure"], 
            data["Total_Expected_Cost"], 
            c=data["Beta"], 
            cmap="viridis", 
            s=100, 
            alpha=0.8,
            edgecolors='k',
            label="Simulation Run"
        )
        

        ax.set_title(f"{model_name} Efficient Frontier", fontsize=14, fontweight='bold')
        ax.set_ylabel("Total Expected Cost (€)", fontsize=12)
        
        if model_name == "Mean-Variance":
            ax.set_xlabel("Variance", fontsize=12)
            ax.set_ylim(500, 1500)
        else:
            ax.set_xlabel("CVaR", fontsize=12)
            
        ax.legend()
        
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label(r'$\beta$', rotation=270, labelpad=15)

    plt.suptitle("Stochastic Demand Economic Dispatch: Risk-Cost Trade-off", fontsize=16)
    plt.tight_layout()
    plt.savefig("efficient_frontier.png")
