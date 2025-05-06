################################
# TAXI - dispatch optimization #
################################
# - ortools
import itertools
from itertools import repeat
from ortools.linear_solver import pywraplp

def ortools_dispatch(active_passenger, empty_vehicle, cost_matrix):
    
    if len(active_passenger) >= len(empty_vehicle):
        A = active_passenger
        B = empty_vehicle
    else: 
        A = empty_vehicle
        B = active_passenger

    
    #Calculate cost matrix
    A_cnt = len(A)
    B_cnt = len(B)
    
    # Declare the MIP solver
    # Create the mip solver with the SCIP backend.
    solver = pywraplp.Solver.CreateSolver('SCIP')

    A_idx = sorted(list(itertools.chain(*list(repeat(list(range(A_cnt)), B_cnt)))))
    B_idx = list(itertools.chain(*list(repeat(list(range(B_cnt)), A_cnt))))

    #Create the variables
    # x[i, j] is an array of 0-1 variables, which will be 1
    # if worker i is assigned to task j.
    x = {}
    for t, p in zip(A_idx, B_idx):
        x[t, p] = solver.IntVar(0, 1, '')

    ## Create the constraints
    #Each worker is assigned to at most 1 task.
    for i in range(A_cnt):
        solver.Add(solver.Sum([x[i, j] for j in range(B_cnt)]) <= 1)

    # Each task is assigned to exactly one worker.
    for j in range(B_cnt):
        solver.Add(solver.Sum([x[i, j] for i in range(A_cnt)]) == 1)
    
    # ### 일정거리 이상인 경우 매칭 제외
    # for i in range(A_cnt):
    #     for j in range(B_cnt):
    #         if cost_matrix[i][j] >= 10: # 10km 이하인 경우만 매칭
    #             solver.Add(x[i, j] <= 0)

    #Create the objective function
    objective_terms = []
    for i in range(A_cnt):
        for j in range(B_cnt):
            objective_terms.append(cost_matrix[i][j] * x[i, j])

    solver.Minimize(solver.Sum(objective_terms))
    #Invoke the solver
    status = solver.Solve()
    # Print solution
    A_iloc = []
    B_iloc = []

    if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:

        for i in range(A_cnt):
            for j in range(B_cnt):

                if x[i, j].solution_value() > 0.5:

                    A_iloc.append(i) 
                    B_iloc.append(j)
    
    iloc_distance = [cost_matrix[iloc_1, iloc_2] for iloc_1, iloc_2 in zip(A_iloc, B_iloc)]
    
    if len(active_passenger) >= len(empty_vehicle):
        dispatch_inf = {'vehicle': B_iloc, 'passenger': A_iloc, 'distance': iloc_distance}
    else:
        dispatch_inf = {'vehicle': A_iloc, 'passenger': B_iloc, 'distance': iloc_distance}    
    
    
    return dispatch_inf


############################
# TAXI - dispatch in-order #
############################
from .dispatch_cost import dispatch_cost_matrix
import numpy as np 
import pandas as pd 
def in_order_dispatch(active_ps, empty_vh, time, simul_configs):
    
    active_passengers = active_ps.copy()
    empty_vehicles = empty_vh.copy()

    vehicle_iloc = []
    passenger_iloc = []
    iloc_distance = []

    for idx, row in active_passengers.iterrows():
        if len(empty_vehicles) != 0:
            row = pd.DataFrame(row).T.reset_index(drop=True)
            
            P_geo = row # passenger
            V_geo = empty_vehicles # vehicles
            
            cost_matrix = dispatch_cost_matrix(P_geo, V_geo, time, simul_configs)
            
            cost_min_idx = np.argmin(cost_matrix)
            vehicle_idx = empty_vehicles.iloc[[cost_min_idx]].index[0]
            
            match_distance = cost_matrix[cost_min_idx]

            empty_vehicles = empty_vehicles.loc[(empty_vehicles.index != vehicle_idx)]
            
            vehicle_iloc.append(vehicle_idx)
            passenger_iloc.append(idx)
            iloc_distance.append(match_distance) 
        else:
            break
        
    dispatch_inf = {'vehicle': vehicle_iloc, 'passenger': passenger_iloc, 'distance': iloc_distance} 
    
    return dispatch_inf