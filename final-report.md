# Cargo Operations Optimization Report

## Executive Summary
This report details the optimization of Express Air's cargo fleet operations. Using a mixed-integer linear programming (MILP) model, we determined the optimal weekly flight schedule for the fleet of 1200 aircraft. The solution achieves a minimum total weekly variable cost of **17,925**, balancing empty repositioning flights and cargo holding costs while ensuring a repeatable weekly cycle.

## Optimization Model
We formulated the problem as a network flow model on a time-expanded graph (Cities $\times$ Days).

### Sets and Variables
*   **Cities**: $N = \{A, B, C\}$
*   **Days**: $T = \{Mon, Tue, Wed, Thu, Fri\}$
*   **Variables**:
    *   $x_{ijt}$: Loaded flights.
    *   $y_{ijt}$: Empty (repositioning) flights.
    *   $I_{it}$: Inventory of idle aircraft.
    *   $H_{ijt}$: Held cargo backlog.

### Constraints
*   **Flow Balance**: Aircraft entering a city (from flight or idle) must equal aircraft leaving.
*   **Demand Satisfaction**: Previous backlog + New Demand = Shipped + New Backlog.
*   **Fleet Capacity**: Total aircraft (in-air + on-ground) $\le$ 1200.
*   **Cyclicity**: Friday's end state connects to Monday's start state.

## Analysis of Results

### Operational Schedule
The optimal schedule utilizes the fleet heavily on Mondays and Fridays.
*   **Total Moves**: 3,300 loaded flights per week.
*   **Empty Repositioning**: Significant repositioning is required, especially from B to C and B to A, costing **15,125** per week.
*   **Cargo Holding**: Cargo is held on the A-B route:
    *   **Monday**: 90 loads held.
    *   **Friday**: 190 loads held.
    *   **Total Holding Cost**: **2,800** per week.

### Fleet Utilization
*   **Peak Usage**: The fleet is 100% utilized (1200 active aircraft) on **Monday** and **Friday**.
*   **Slack Capacity**: There is excess capacity on Wednesday (330 idle aircraft) and Tuesday (20 idle).
*   **Bottleneck**: The fleet size is the primary constraint preventing full on-time delivery. The holding cost is incurred not because it is cheaper than flying, but because there are literally no aircraft available to fly the cargo on Mon/Fri.

## Managerial Implications

### 1. Fleet Size Expansion
The current fleet of 1200 is a hard constraint during peak demand (Mon/Fri).
*   **Recommendation**: Investigate leasing or acquiring additional aircraft. Even 50-100 more aircraft could eliminate the A-B backlog.
*   **Benefit**: Eliminating the backlog (280 loads * 10 cost = 2800 savings) vs cost of new planes.

### 2. Demand Management
The demand "bunching" on A-B (Fri 300, Mon 100 + Fri backlog) causes the issues.
*   **Recommendation**: If possible, incentivize customers to shift A-B shipments to mid-week (Wed/Thu) where capacity exists.

### 3. Route Balance
There is a massive imbalance requiring empty flights out of B.
*   **Recommendation**: Sales efforts should focus on increasing outbound cargo from B (B-A and B-C demand is very low: 25/day) to utilize the empty flights (e.g. Mon B-A has 275 empty flights). Filling these empty legs generates pure revenue with zero additional flight cost.
