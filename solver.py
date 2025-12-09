import gurobipy as gp
from gurobipy import GRB

# --- Data ---
AIRPORTS = ['A', 'B', 'C']
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
T = len(DAYS)

# Demand: D[i][j][day_idx]
# Table 1: Arrivals
#       M    T    W    Th   F
# A-B  100  200  100  400  300
# A-C   50   50   50   50   50
# B-A   25   25   25   25   25
# B-C   25   25   25   25   25
# C-A   40   40   40   40   40
# C-B  400  200  300  200  400

DEMAND = {
    ('A', 'B'): [100, 200, 100, 400, 300],
    ('A', 'C'): [ 50,  50,  50,  50,  50],
    ('B', 'A'): [ 25,  25,  25,  25,  25],
    ('B', 'C'): [ 25,  25,  25,  25,  25],
    ('C', 'A'): [ 40,  40,  40,  40,  40],
    ('C', 'B'): [400, 200, 300, 200, 400],
}

# Add 0 demand for self-loops or non-existent pairs if needed, 
# but we iterate over keys of DEMAND for valid cargo routes.
# Valid airport routes for aircraft (A->B, B->A, etc.) are all pairs.
ROUTES = [(i, j) for i in AIRPORTS for j in AIRPORTS if i != j]

# Repo Cost C_empty
# A <-> B: 7
# A <-> C: 3
# B <-> C: 6
COST_REPO = {
    ('A', 'B'): 7, ('B', 'A'): 7,
    ('A', 'C'): 3, ('C', 'A'): 3,
    ('B', 'C'): 6, ('C', 'B'): 6
}

COST_HOLD = 10
FLEET_SIZE = 1200

# --- Model ---
model = gp.Model("CargoOperations")

# --- Variables ---
# x[i,j,t]: Loaded aircraft i->j on day t (start of day t, arrive start of t+1)
x = model.addVars(ROUTES, range(T), vtype=GRB.INTEGER, name="x")

# y[i,j,t]: Empty aircraft i->j on day t
y = model.addVars(ROUTES, range(T), vtype=GRB.INTEGER, name="y")

# I[i,t]: Inventory at airport i (idle from day t to t+1)
# Aircraft staying on ground at i during day t.
I = model.addVars(AIRPORTS, range(T), vtype=GRB.INTEGER, name="I")

# H[i,j,t]: Held cargo (backlog) for route i->j at END of day t
# Only defined for routes with demand.
H = model.addVars(DEMAND.keys(), range(T), vtype=GRB.INTEGER, name="H")

# --- Objective ---
# Minimize Repo Cost + Holding Cost
# Repo: sum(COST_REPO[i,j] * y[i,j,t])
# Hold: sum(COST_HOLD * H[i,j,t])

obj_repo = gp.quicksum(COST_REPO[i,j] * y[i,j,t] for i,j in ROUTES for t in range(T))
obj_hold = gp.quicksum(COST_HOLD * H[i,j,t] for (i,j) in DEMAND.keys() for t in range(T))

model.setObjective(obj_repo + obj_hold, GRB.MINIMIZE)

# --- Constraints ---

# Helper for cyclic previous day index
def prev(t):
    return (t - 1) % T

# 1. Aircraft Flow Balance
# For each airport i, day t:
#   Inbound from prev day (loaded + empty) + Inventory from prev day
#   = Outbound current day (loaded + empty) + Inventory current day
for i in AIRPORTS:
    for t in range(T):
        inbound = gp.quicksum(x[j, i, prev(t)] + y[j, i, prev(t)] for j in AIRPORTS if j != i)
        prev_inv = I[i, prev(t)]
        
        outbound = gp.quicksum(x[i, j, t] + y[i, j, t] for j in AIRPORTS if j != i)
        curr_inv = I[i, t]
        
        model.addConstr(inbound + prev_inv == outbound + curr_inv, name=f"FlowBal_Air_{i}_{DAYS[t]}")

# 2. Cargo Flow Balance
# For each demand route i->j, day t:
#   Backlog from prev day + New Demand
#   = Shipped (x[i,j,t]) + Backlog current day
for (i, j), d_vals in DEMAND.items():
    for t in range(T):
        backlog_prev = H[i, j, prev(t)]
        new_demand = d_vals[t]
        
        shipped = x[i, j, t]
        backlog_curr = H[i, j, t]
        
        model.addConstr(backlog_prev + new_demand == shipped + backlog_curr, name=f"FlowBal_Cargo_{i}_{j}_{DAYS[t]}")

# 3. Fleet Size
# Total aircraft = 1200
# Sum of all aircraft "in the system".
# Aircraft are either:
#  - In the air (departed day t, arrive day t+1) -> x[..,t] + y[..,t]
#  - On the ground (idle day t, available day t+1) -> I[..,t]
# This sum must equal Fleet Size for every day.
# (If we sum for day t, we count all aircraft existing during day t).
for t in range(T):
    total_in_air = gp.quicksum(x[i, j, t] + y[i, j, t] for i, j in ROUTES)
    total_on_ground = gp.quicksum(I[i, t] for i in AIRPORTS)
    model.addConstr(total_in_air + total_on_ground == FLEET_SIZE, name=f"FleetSize_{DAYS[t]}")

# --- Solve ---
model.optimize()

# --- Output ---
if model.status == GRB.OPTIMAL:
    print(f"\nObjective Value: {model.objVal}")
    
    print("\n--- Weekly Schedule ---")
    print(f"{'Day':<5} {'Origin':<6} {'Dest':<6} {'Loaded':<8} {'Empty':<8} {'Held':<8}")
    for t in range(T):
        print(f"--- {DAYS[t]} ---")
        for i, j in ROUTES:
            val_x = x[i, j, t].X
            val_y = y[i, j, t].X
            val_h = 0
            if (i, j) in DEMAND:
                val_h = H[i, j, t].X
            
            if val_x > 0 or val_y > 0 or val_h > 0:
                print(f"{DAYS[t]:<5} {i:<6} {j:<6} {val_x:<8.0f} {val_y:<8.0f} {val_h:<8.0f}")
        for i in AIRPORTS:
            val_i = I[i, t].X
            if val_i > 0:
                print(f"{DAYS[t]:<5} {i:<6} {'-':<6} {'-':<8} {'-':<8} {'-':<8} (Idle at {i}: {val_i:.0f})")

    # Metrics
    total_shipped = sum(x[i,j,t].X for i,j in ROUTES for t in range(T))
    total_demand = sum(sum(d) for d in DEMAND.values())
    total_empty_cost = obj_repo.getValue()
    total_hold_cost = obj_hold.getValue()
    
    print("\n--- Summary Metrics ---")
    print(f"Total Cost: {model.objVal}")
    print(f"Total Loaded Flights: {total_shipped}")
    print(f"Total Demand: {total_demand}")
    print(f"Repositioning Cost: {total_empty_cost}")
    print(f"Holding Cost: {total_hold_cost}")

else:
    print("Optimization was not successful.")
