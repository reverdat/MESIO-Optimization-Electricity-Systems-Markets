import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import numpy as np
from pyomo.environ import value

def plot_single_period_auction(instance):
    """
    Plot aggregated supply and demand curves for single-period auction model.
    Highlights accepted blocks, social welfare, and energy exchanged.
    
    Parameters:
    -----------
    instance : Pyomo ConcreteModel instance
        Solved single-period model instance
    """
    
    # Extract data from single-period model (no time index)
    supply_blocks = []
    demand_blocks = []
    
    # Collect supply bids
    for i in instance.G:
        for k in instance.B_G:
            power = value(instance.P_B_G[i, k])
            price = value(instance.Lambda_B_G[i, k])
            accepted = value(instance.P_G[i, k])
            supply_blocks.append({
                'generator': i,
                'block': k,
                'power': power,
                'price': price,
                'accepted': accepted
            })
    
    # Collect demand bids
    for d in instance.D:
        for k in instance.B_D:
            power = value(instance.P_B_D[d, k])
            price = value(instance.Lambda_B_D[d, k])
            accepted = value(instance.P_D[d, k])
            demand_blocks.append({
                'demand': d,
                'block': k,
                'power': power,
                'price': price,
                'accepted': accepted
            })
    
    # Sort supply blocks by price (ascending - merit order)
    supply_blocks.sort(key=lambda x: x['price'])
    
    # Sort demand blocks by price (descending)
    demand_blocks.sort(key=lambda x: x['price'], reverse=True)
    
    # Create supply curve (cumulative power)
    supply_cumulative = [0]
    supply_prices = []
    supply_accepted = []
    
    for block in supply_blocks:
        supply_cumulative.append(supply_cumulative[-1] + block['power'])
        supply_prices.append(block['price'])
        supply_accepted.append(block['accepted'])
    
    # Create demand curve
    demand_cumulative = [0]
    demand_prices = []
    demand_accepted = []
    
    for block in demand_blocks:
        demand_cumulative.append(demand_cumulative[-1] + block['power'])
        demand_prices.append(block['price'])
        demand_accepted.append(block['accepted'])
    
    # Calculate total energy exchanged
    total_energy = sum(value(instance.P_D[d, k]) for d in instance.D for k in instance.B_D)
    
    # Calculate social welfare (objective value)
    social_welfare = value(instance.obj)
    
    # Calculate market clearing price (weighted average of accepted generation)
    total_gen_cost = sum(value(instance.Lambda_B_G[i, k] * instance.P_G[i, k]) 
                        for i in instance.G for k in instance.B_G)
    total_gen_power = sum(value(instance.P_G[i, k]) 
                         for i in instance.G for k in instance.B_G)
    clearing_price = total_gen_cost / total_gen_power if total_gen_power > 0 else 0
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 9))
    
    # Build step functions for supply curve
    x_supply = []
    y_supply = []
    for i in range(len(supply_prices)):
        x_supply.extend([supply_cumulative[i], supply_cumulative[i+1]])
        y_supply.extend([supply_prices[i], supply_prices[i]])
    
    # Build step functions for demand curve
    x_demand = []
    y_demand = []
    for i in range(len(demand_prices)):
        x_demand.extend([demand_cumulative[i], demand_cumulative[i+1]])
        y_demand.extend([demand_prices[i], demand_prices[i]])
    
    # Plot curves
    ax.plot(x_supply, y_supply, 'r-', linewidth=2.5, label='Supply Curve (Merit Order)', 
            marker='o', markersize=5, markerfacecolor='red', markeredgecolor='darkred')
    ax.plot(x_demand, y_demand, 'b-', linewidth=2.5, label='Demand Curve', 
            marker='s', markersize=5, markerfacecolor='blue', markeredgecolor='darkblue')
    
    # Highlight accepted supply blocks (green)
    x_pos = 0
    for i, block in enumerate(supply_blocks):
        # Draw all blocks with light outline
        rect_all = Rectangle((x_pos, 0), block['power'], block['price'], 
                            facecolor='white', edgecolor='red', 
                            alpha=0.3, linewidth=1, linestyle=':')
        ax.add_patch(rect_all)
        
        if block['accepted'] > 0.01:  # Threshold for numerical precision
            width = block['accepted']
            height = block['price']
            rect = Rectangle((x_pos, 0), width, height, 
                           facecolor='lightgreen', edgecolor='darkgreen', 
                           alpha=0.7, linewidth=2)
            ax.add_patch(rect)
            
            # Add label
            ax.text(x_pos + width/2, height/2, 
                   f'G{block["generator"]}-B{block["block"]}\n{width:.1f}MW', 
                   ha='center', va='center', fontsize=8, fontweight='bold')
        
        x_pos += block['power']
    
    # Highlight accepted demand blocks (light blue)
    x_pos = 0
    max_price = max(demand_prices + supply_prices) if (demand_prices and supply_prices) else 30
    for i, block in enumerate(demand_blocks):
        # Draw all blocks with light outline
        rect_all = Rectangle((x_pos, block['price']), block['power'], 
                            max_price - block['price'], 
                            facecolor='white', edgecolor='blue', 
                            alpha=0.3, linewidth=1, linestyle=':')
        ax.add_patch(rect_all)
        
        if block['accepted'] > 0.01:
            width = block['accepted']
            rect = Rectangle((x_pos, clearing_price), width, block['price'] - clearing_price, 
                           facecolor='lightblue', edgecolor='darkblue', 
                           alpha=0.6, linewidth=2)
            ax.add_patch(rect)
            
            # Add label
            ax.text(x_pos + width/2, (block['price'] + clearing_price)/2, 
                   f'D{block["demand"]}-B{block["block"]}\n{width:.1f}MW', 
                   ha='center', va='center', fontsize=8, fontweight='bold')
        
        x_pos += block['power']
    
    # Shade social welfare area
    if total_energy > 0:
        # Producer surplus (below clearing price, above supply)
        x_pos = 0
        for block in supply_blocks:
            if block['accepted'] > 0.01:
                width = block['accepted']
                surplus_height = clearing_price - block['price']
                if surplus_height > 0:
                    rect = Rectangle((x_pos, block['price']), width, surplus_height,
                                   facecolor='pink', alpha=0.4, edgecolor='red', 
                                   linewidth=1.5, linestyle='--', 
                                   label='Producer Surplus' if x_pos == 0 else '')
                    ax.add_patch(rect)
            x_pos += block['power']
        
        # Consumer surplus (above clearing price, below demand)
        x_pos = 0
        for block in demand_blocks:
            if block['accepted'] > 0.01:
                width = block['accepted']
                surplus_height = block['price'] - clearing_price
                if surplus_height > 0:
                    rect = Rectangle((x_pos, clearing_price), width, surplus_height,
                                   facecolor='yellow', alpha=0.4, edgecolor='orange', 
                                   linewidth=1.5, linestyle='--', 
                                   label='Consumer Surplus' if x_pos == 0 else '')
                    ax.add_patch(rect)
            x_pos += block['power']
        
        # Draw clearing price line
        ax.axhline(y=clearing_price, color='purple', linestyle='--', 
                  linewidth=3, label=f'Market Clearing Price = ${clearing_price:.2f}/MWh',
                  alpha=0.8)
    
    # Mark total energy exchanged
    ax.axvline(x=total_energy, color='green', linestyle=':', 
              linewidth=3, label=f'Energy Exchanged = {total_energy:.2f} MW',
              alpha=0.8)
    
    # Add text box with key metrics
    textstr = '═══ MARKET RESULTS ═══\n'
    textstr += f'Energy Exchanged: {total_energy:.2f} MW\n'
    textstr += f'Social Welfare: ${social_welfare:.2f}\n'
    textstr += f'Clearing Price: ${clearing_price:.2f}/MWh\n'
    textstr += '─────────────────────\n'
    
    # Generator status
    textstr += 'Generator Status:\n'
    for i in instance.G:
        total_gen = sum(value(instance.P_G[i, k]) for k in instance.B_G)
        textstr += f'  G{i}: {"ON"} ({total_gen:.1f} MW)\n'
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.9, edgecolor='black', linewidth=2)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', bbox=props, family='monospace', fontweight='bold')
    
    # Labels and formatting
    ax.set_xlabel('Cumulative Power (MW)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Price ($/MWh)', fontsize=13, fontweight='bold')
    ax.set_title('Single-Period Market Clearing\nSupply-Demand Equilibrium', 
                fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.7)
    ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # Set axis limits
    x_max = max(max(supply_cumulative), max(demand_cumulative)) * 1.15
    y_max = max(supply_prices + demand_prices) * 1.15
    ax.set_xlim(left=0, right=x_max)
    ax.set_ylim(bottom=0, top=y_max)
    
    plt.tight_layout()
    return fig, ax


def plot_multiperiod_auction(instance):
    """
    Plot aggregated supply and demand curves for multi-period auction model.
    Creates separate subplots for each time period.
    
    Parameters:
    -----------
    instance : Pyomo ConcreteModel instance
        Solved multi-period model instance
    """
    
    n_periods = len(list(instance.T))
    
    # Create subplots
    fig, axes = plt.subplots(1, n_periods, figsize=(10*n_periods, 8))
    
    # Handle single period case
    if n_periods == 1:
        axes = [axes]
    
    # Calculate total social welfare
    total_sw = value(instance.obj)
    
    for idx, t in enumerate(instance.T):
        ax = axes[idx]
        
        # Extract data for period t
        supply_blocks = []
        demand_blocks = []
        
        # Collect supply bids
        for i in instance.G:
            for k in instance.B_G:
                power = value(instance.P_B_G[i, t, k])
                price = value(instance.Lambda_B_G[i, t, k])
                accepted = value(instance.P_G[i, t, k])
                supply_blocks.append({
                    'generator': i,
                    'block': k,
                    'power': power,
                    'price': price,
                    'accepted': accepted
                })
        
        # Collect demand bids
        for d in instance.D:
            for k in instance.B_D:
                power = value(instance.P_B_D[d, t, k])
                price = value(instance.Lambda_B_D[d, t, k])
                accepted = value(instance.P_D[d, t, k])
                demand_blocks.append({
                    'demand': d,
                    'block': k,
                    'power': power,
                    'price': price,
                    'accepted': accepted
                })
        
        # Sort blocks
        supply_blocks.sort(key=lambda x: x['price'])
        demand_blocks.sort(key=lambda x: x['price'], reverse=True)
        
        # Create cumulative curves
        supply_cumulative = [0]
        supply_prices = []
        for block in supply_blocks:
            supply_cumulative.append(supply_cumulative[-1] + block['power'])
            supply_prices.append(block['price'])
        
        demand_cumulative = [0]
        demand_prices = []
        for block in demand_blocks:
            demand_cumulative.append(demand_cumulative[-1] + block['power'])
            demand_prices.append(block['price'])
        
        # Calculate metrics for this period
        total_energy = value(instance.P_D_total[1, t])  # Assuming single demand
        
        sw_period = (sum(value(instance.Lambda_B_D[d, t, k] * instance.P_D[d, t, k]) 
                        for d in instance.D for k in instance.B_D) -
                    sum(value(instance.Lambda_B_G[i, t, k] * instance.P_G[i, t, k]) 
                        for i in instance.G for k in instance.B_G)) * value(instance.delta_t)
        
        total_gen_cost = sum(value(instance.Lambda_B_G[i, t, k] * instance.P_G[i, t, k]) 
                            for i in instance.G for k in instance.B_G)
        total_gen_power = sum(value(instance.P_G[i, t, k]) 
                             for i in instance.G for k in instance.B_G)
        clearing_price = total_gen_cost / total_gen_power if total_gen_power > 0 else 0
        
        # Build step functions
        x_supply, y_supply = [], []
        for i in range(len(supply_prices)):
            x_supply.extend([supply_cumulative[i], supply_cumulative[i+1]])
            y_supply.extend([supply_prices[i], supply_prices[i]])
        
        x_demand, y_demand = [], []
        for i in range(len(demand_prices)):
            x_demand.extend([demand_cumulative[i], demand_cumulative[i+1]])
            y_demand.extend([demand_prices[i], demand_prices[i]])
        
        # Plot curves
        ax.plot(x_supply, y_supply, 'r-', linewidth=2.5, label='Supply', 
                marker='o', markersize=4)
        ax.plot(x_demand, y_demand, 'b-', linewidth=2.5, label='Demand', 
                marker='s', markersize=4)
        
        # Highlight accepted supply blocks
        x_pos = 0
        for block in supply_blocks:
            # Draw all blocks
            rect_all = Rectangle((x_pos, 0), block['power'], block['price'], 
                                facecolor='white', edgecolor='red', 
                                alpha=0.3, linewidth=1, linestyle=':')
            ax.add_patch(rect_all)
            
            if block['accepted'] > 0.01:
                rect = Rectangle((x_pos, 0), block['accepted'], block['price'], 
                               facecolor='lightgreen', edgecolor='darkgreen', 
                               alpha=0.7, linewidth=2)
                ax.add_patch(rect)
                
                ax.text(x_pos + block['accepted']/2, block['price']/2, 
                       f'G{block["generator"]}-B{block["block"]}\n{block["accepted"]:.1f}', 
                       ha='center', va='center', fontsize=7, fontweight='bold')
            
            x_pos += block['power']
        
        # Highlight accepted demand blocks
        x_pos = 0
        max_price = max(demand_prices + supply_prices) if (demand_prices and supply_prices) else 30
        for block in demand_blocks:
            rect_all = Rectangle((x_pos, block['price']), block['power'], 
                                max_price - block['price'], 
                                facecolor='white', edgecolor='blue', 
                                alpha=0.3, linewidth=1, linestyle=':')
            ax.add_patch(rect_all)
            
            if block['accepted'] > 0.01:
                rect = Rectangle((x_pos, clearing_price), block['accepted'], 
                               block['price'] - clearing_price, 
                               facecolor='lightblue', edgecolor='darkblue', 
                               alpha=0.6, linewidth=2)
                ax.add_patch(rect)
                
                ax.text(x_pos + block['accepted']/2, 
                       (block['price'] + clearing_price)/2, 
                       f'D{block["demand"]}-B{block["block"]}\n{block["accepted"]:.1f}', 
                       ha='center', va='center', fontsize=7, fontweight='bold')
            
            x_pos += block['power']
        
        # Shade surplus areas
        if total_energy > 0:
            # Producer surplus
            x_pos = 0
            for block in supply_blocks:
                if block['accepted'] > 0.01:
                    surplus_height = clearing_price - block['price']
                    if surplus_height > 0:
                        rect = Rectangle((x_pos, block['price']), block['accepted'], 
                                       surplus_height, facecolor='pink', alpha=0.4, 
                                       edgecolor='red', linewidth=1, linestyle='--')
                        ax.add_patch(rect)
                x_pos += block['power']
            
            # Consumer surplus
            x_pos = 0
            for block in demand_blocks:
                if block['accepted'] > 0.01:
                    surplus_height = block['price'] - clearing_price
                    if surplus_height > 0:
                        rect = Rectangle((x_pos, clearing_price), block['accepted'], 
                                       surplus_height, facecolor='yellow', alpha=0.4, 
                                       edgecolor='orange', linewidth=1, linestyle='--')
                        ax.add_patch(rect)
                x_pos += block['power']
            
            # Clearing price line
            ax.axhline(y=clearing_price, color='purple', linestyle='--', 
                      linewidth=2.5, alpha=0.7)
        
        # Energy exchanged line
        ax.axvline(x=total_energy, color='green', linestyle=':', 
                  linewidth=2.5, alpha=0.7)
        
        # Text box with metrics
        textstr = f'══ PERIOD t={t} ══\n'
        textstr += f'Energy: {total_energy:.2f} MW\n'
        textstr += f'SW: ${sw_period:.2f}\n'
        textstr += f'Price: ${clearing_price:.2f}/MWh\n'
        textstr += '─────────────\n'
        
        for i in instance.G:
            u_val = value(instance.u[i, t])
            total_gen = value(instance.P_G_total[i, t])
            textstr += f'G{i}: {"ON" if u_val > 0.5 else "OFF"} ({total_gen:.1f})\n'
        
        # Show ramp from previous period
        if t > min(instance.T):
            textstr += '─────────────\n'
            textstr += 'Ramps:\n'
            for i in instance.G:
                if t == min(instance.T):
                    ramp = value(instance.P_G_total[i, t]) - value(instance.P_0[i])
                    textstr += f'G{i}: {ramp:+.1f}\n'
                else:
                    t_prev = list(instance.T)[list(instance.T).index(t) - 1]
                    ramp = value(instance.P_G_total[i, t]) - value(instance.P_G_total[i, t_prev])
                    textstr += f'G{i}: {ramp:+.1f}\n'
        
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.9, 
                    edgecolor='black', linewidth=1.5)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=props, family='monospace', 
                fontweight='bold')
        
        # Formatting
        ax.set_xlabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Price ($/MWh)', fontsize=11, fontweight='bold')
        ax.set_title(f'Period t={t}', fontsize=13, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=0.7)
        ax.legend(fontsize=9, loc='upper right', framealpha=0.9)
        
        x_max = max(max(supply_cumulative), max(demand_cumulative)) * 1.15
        y_max = max(supply_prices + demand_prices) * 1.15
        ax.set_xlim(left=0, right=x_max)
        ax.set_ylim(bottom=0, top=y_max)
    
    # Add overall title
    fig.suptitle(f'Multi-Period Market Clearing | Total Social Welfare: ${total_sw:.2f}', 
                fontsize=16, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    return fig, axes