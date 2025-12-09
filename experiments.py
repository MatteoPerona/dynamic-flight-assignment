import copy
from solver import solve_cargo_operations, DEFAULT_DEMAND

def run_fleet_experiments():
    print("\n=== Experiment 1: Fleet Size Sensitivity ===")
    print(f"{'Fleet Size':<12} {'Total Cost':<12} {'Repo Cost':<12} {'Hold Cost':<12} {'Backlog Days':<12}")
    
    fleet_sizes = range(1150, 1451, 50)
    results = []
    
    for fs in fleet_sizes:
        res = solve_cargo_operations(fleet_size=fs, verbose=False)
        if res:
            print(f"{fs:<12} {res['Total Cost']:<12.0f} {res['Repo Cost']:<12.0f} {res['Hold Cost']:<12.0f} {res['Backlog Days']:<12.0f}")
            results.append((fs, res))
        else:
            print(f"{fs:<12} {'Infeasible':<12}")

def run_demand_experiments():
    print("\n=== Experiment 2: Demand Smoothing ===")
    print("Moving 50 loads of A->B demand from Monday (peak) to Wednesday (slack).")
    
    # Original A->B: [100, 200, 100, 400, 300]
    # Note: Fri backlog (190) + Mon demand (100) = 290. 
    # Bottleneck is fleet.
    # Let's try to flatten demand.
    
    modified_demand = copy.deepcopy(DEFAULT_DEMAND)
    # A->B demand
    # Mon: 100 -> 50
    # Wed: 100 -> 150
    modified_demand[('A', 'B')][0] -= 50
    modified_demand[('A', 'B')][2] += 50
    
    print("\n-- Baseline (Fleet=1200) --")
    base = solve_cargo_operations(fleet_size=1200, verbose=False)
    print(f"Cost: {base['Total Cost']}, Backlog Days: {base['Backlog Days']}")
    
    print("\n-- Smoothed Demand (Fleet=1200) --")
    smooth = solve_cargo_operations(fleet_size=1200, demand_override=modified_demand, verbose=False)
    
    if smooth:
        print(f"Cost: {smooth['Total Cost']}, Backlog Days: {smooth['Backlog Days']}")
        savings = base['Total Cost'] - smooth['Total Cost']
        print(f"Savings from smoothing: {savings}")
    else:
        print("Infeasible with smoothed demand.")

def run_route_balance_experiments():
    print("\n=== Experiment 3: Route Balancing (Utilization of Empty Legs) ===")
    print("Monday has 275 empty flights from B->A. Testing impact of adding 200 loads of new demand to B->A on Monday.")
    
    modified_demand = copy.deepcopy(DEFAULT_DEMAND)
    # B->A original: [25, 25, 25, 25, 25]
    # Add 200 to Monday
    modified_demand[('B', 'A')][0] += 200
    
    print("\n-- Baseline (Fleet=1200) --")
    base = solve_cargo_operations(fleet_size=1200, verbose=False)
    print(f"Total Cost: {base['Total Cost']}, Repo Cost: {base['Repo Cost']}")
    
    print("\n-- Increased B->A Demand (+200 on Mon) --")
    new_scenario = solve_cargo_operations(fleet_size=1200, demand_override=modified_demand, verbose=False)
    
    if new_scenario:
        print(f"Total Cost: {new_scenario['Total Cost']}, Repo Cost: {new_scenario['Repo Cost']}")
        cost_diff = new_scenario['Total Cost'] - base['Total Cost']
        print(f"Change in Objective Cost: {cost_diff}")
        print("Note: Cost DECREASES because we replace Empty Flights (Cost=7) with Loaded Flights (Cost=0 in this objective).")
        print("This confirms we can carry extra cargo essentially for 'free' (or better) operational variable cost.")
    else:
        print("Infeasible.")

if __name__ == "__main__":
    run_fleet_experiments()
    run_demand_experiments()
    run_route_balance_experiments()
