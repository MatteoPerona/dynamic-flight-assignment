import gurobipy as gp
from gurobipy import GRB

# --- Data ---
AIRPORTS = ['A', 'B', 'C']
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
T = len(DAYS)

# Demand: D[i][j][day_idx]
DEFAULT_DEMAND = {
    ('A', 'B'): [100, 200, 100, 400, 300],
    ('A', 'C'): [ 50,  50,  50,  50,  50],
    ('B', 'A'): [ 25,  25,  25,  25,  25],
    ('B', 'C'): [ 25,  25,  25,  25,  25],
    ('C', 'A'): [ 40,  40,  40,  40,  40],
    ('C', 'B'): [400, 200, 300, 200, 400],
}

ROUTES = [(i, j) for i in AIRPORTS for j in AIRPORTS if i != j]

COST_REPO = {
    ('A', 'B'): 7, ('B', 'A'): 7,
    ('A', 'C'): 3, ('C', 'A'): 3,
    ('B', 'C'): 6, ('C', 'B'): 6
}

COST_HOLD = 10

def solve_cargo_operations(fleet_size=1200, demand_override=None, verbose=True):
    """
    Solves the Cargo Operations problem.
    
    Args:
        fleet_size (int): Total number of aircraft.
        demand_override (dict): Optional replacement for DEFAULT_DEMAND.
        verbose (bool): Whether to print solution details.
        
    Returns:
        dict: Summary metrics (Cost, RepoCost, HoldCost, TotalShipped, BacklogDays) or None if infeasible.
    """
    demand = demand_override if demand_override else DEFAULT_DEMAND
    
    # --- Model ---
    # Suppress output if not verbose
    env = gp.Env(empty=True)
    if not verbose:
        env.setParam('OutputFlag', 0)
    else:
        env.setParam('OutputFlag', 1)
    env.start()
    
    model = gp.Model("CargoOperations", env=env)

    # --- Variables ---
    x = model.addVars(ROUTES, range(T), vtype=GRB.INTEGER, name="x")
    y = model.addVars(ROUTES, range(T), vtype=GRB.INTEGER, name="y")
    I = model.addVars(AIRPORTS, range(T), vtype=GRB.INTEGER, name="I")
    H = model.addVars(demand.keys(), range(T), vtype=GRB.INTEGER, name="H")

    # --- Objective ---
    obj_repo = gp.quicksum(COST_REPO[i,j] * y[i,j,t] for i,j in ROUTES for t in range(T))
    obj_hold = gp.quicksum(COST_HOLD * H[i,j,t] for (i,j) in demand.keys() for t in range(T))
    model.setObjective(obj_repo + obj_hold, GRB.MINIMIZE)

    # --- Constraints ---
    def prev(t):
        return (t - 1) % T

    # 1. Aircraft Flow Balance
    for i in AIRPORTS:
        for t in range(T):
            inbound = gp.quicksum(x[j, i, prev(t)] + y[j, i, prev(t)] for j in AIRPORTS if j != i)
            prev_inv = I[i, prev(t)]
            outbound = gp.quicksum(x[i, j, t] + y[i, j, t] for j in AIRPORTS if j != i)
            curr_inv = I[i, t]
            model.addConstr(inbound + prev_inv == outbound + curr_inv, name=f"FlowBal_Air_{i}_{DAYS[t]}")

    # 2. Cargo Flow Balance
    for (i, j), d_vals in demand.items():
        for t in range(T):
            backlog_prev = H[i, j, prev(t)]
            new_demand = d_vals[t]
            shipped = x[i, j, t]
            backlog_curr = H[i, j, t]
            model.addConstr(backlog_prev + new_demand == shipped + backlog_curr, name=f"FlowBal_Cargo_{i}_{j}_{DAYS[t]}")

    # 3. Fleet Size
    for t in range(T):
        total_in_air = gp.quicksum(x[i, j, t] + y[i, j, t] for i, j in ROUTES)
        total_on_ground = gp.quicksum(I[i, t] for i in AIRPORTS)
        model.addConstr(total_in_air + total_on_ground == fleet_size, name=f"FleetSize_{DAYS[t]}")

    # --- Solve ---
    model.optimize()

    # --- Output ---
    if model.status == GRB.OPTIMAL:
        repo_cost = obj_repo.getValue()
        hold_cost = obj_hold.getValue()
        total_shipped = sum(x[i,j,t].X for i,j in ROUTES for t in range(T))
        total_backlog_days = sum(H[i,j,t].X for i,j in demand.keys() for t in range(T)) # Sum of H is total backlog-days
        
        if verbose:
            print(f"\nObjective Value: {model.objVal}")
            print("\n--- Weekly Schedule ---")
            print(f"{'Day':<5} {'Origin':<6} {'Dest':<6} {'Loaded':<8} {'Empty':<8} {'Held':<8}")
            for t in range(T):
                print(f"--- {DAYS[t]} ---")
                for i, j in ROUTES:
                    val_x = x[i, j, t].X
                    val_y = y[i, j, t].X
                    val_h = 0
                    if (i, j) in demand:
                        val_h = H[i, j, t].X
                    if val_x > 0 or val_y > 0 or val_h > 0:
                        print(f"{DAYS[t]:<5} {i:<6} {j:<6} {val_x:<8.0f} {val_y:<8.0f} {val_h:<8.0f}")
                for i in AIRPORTS:
                    val_i = I[i, t].X
                    if val_i > 0:
                         print(f"{DAYS[t]:<5} {i:<6} {'-':<6} {'-':<8} {'-':<8} {'-':<8} (Idle at {i}: {val_i:.0f})")

            print("\n--- Summary Metrics ---")
            print(f"Total Cost: {model.objVal}")
            print(f"Total Loaded Flights: {total_shipped}")
            print(f"Repositioning Cost: {repo_cost}")
            print(f"Holding Cost: {hold_cost}")
            
        return {
            "Total Cost": model.objVal,
            "Repo Cost": repo_cost,
            "Hold Cost": hold_cost,
            "Backlog Days": total_backlog_days
        }
    else:
        if verbose:
            print("Optimization was not successful.")
        return None

if __name__ == "__main__":
    solve_cargo_operations(verbose=True)
