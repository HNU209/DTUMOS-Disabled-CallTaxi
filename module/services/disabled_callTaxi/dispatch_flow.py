import sys
sys.path.append("..")
#### dispatch helper 
from module.osrm_routing import osrm_routing_machine
from module.utils import calculate_straight_distance
from module.simulator_helper import save_json_data
from multiprocess import Pool
import numpy as np 

### Changing travel time to eta result
def change_travel_time_to_eta_result(data, time, simul_configs):
    
    YMD = simul_configs['YMD']
    eta_model = simul_configs['eta_model']

    ## convert to ETA input format
    #- numerical variable 
    target_minute = time%60
    target_hour = time//60

    target_weekday = YMD.weekday()
    target_holiday = 1 if target_weekday >= 5 else 0
    
    #- categorical variable 
    ride_lat = data[:,0]
    ride_lon = data[:,1]

    alight_lat = data[:,2]
    alight_lon = data[:,3]
    
    eta_inputData = pd.DataFrame({"minute":target_minute, 'hour':target_hour, 'weekday': target_weekday, 'holiday':target_holiday, 
                                  "ride_lat":ride_lat, "ride_lon":ride_lon, 'alight_lat':alight_lat, 'alight_lon':alight_lon})
    
    eta_inputData['minute'] = eta_inputData['minute'].astype('category')
    eta_inputData['hour'] = eta_inputData['hour'].astype('category')
    eta_inputData['weekday'] = eta_inputData['weekday'].astype('category')
    eta_inputData['holiday'] = eta_inputData['holiday'].astype('category')

    if simul_configs['relocation_region'] == 'metro':
        eta_inputData['straight_distance'] = \
            calculate_straight_distance(eta_inputData['ride_lat'].values, 
                                        eta_inputData['ride_lon'].values,
                                        eta_inputData['alight_lat'].values,
                                        eta_inputData['alight_lon'].values)
        osrm_rs = [osrm_routing_machine([row['ride_lat'], row['ride_lon'], row['alight_lat'], row['alight_lon']])\
            for _, row in eta_inputData.iterrows()]
        eta_inputData['osrm_distance'] = [rs['distance'] / 1000 if rs != None else 0.5 for rs in osrm_rs]
        eta_inputData = eta_inputData[['weekday', 'holiday', 'hour', 'minute', 'straight_distance', 'osrm_distance']]   

    ## predict => eta result
    eta_result = eta_model.predict(eta_inputData)
    
    return eta_result


def address_current_active_vehicle(current_active_vehicle, time, save_path, simul_configs):

    # 0. osrm 경로 추출
    O = current_active_vehicle[['lat', 'lon', 'P_ride_lat', 'P_ride_lon']].values
    D = current_active_vehicle[['P_ride_lat', 'P_ride_lon', 'P_alight_lat', 'P_alight_lon']].values
    
    if len(O) >= 60:
        p = Pool(processes=30)
        routing_result_O = p.map(osrm_routing_machine, O)
        routing_result_D = p.map(osrm_routing_machine, D)
        del p
    else:
        routing_result_O = [osrm_routing_machine(o) for o in O]
        routing_result_D = [osrm_routing_machine(d) for d in D]

    # 1. ETA model이 있으면 적용하여 travel time 조정
    if simul_configs['eta_model'] != None: 
        
        eta_result_O = change_travel_time_to_eta_result(O, time, simul_configs)
        eta_result_D = change_travel_time_to_eta_result(D, time, simul_configs)
        
        for idx in range(len(current_active_vehicle)):
            ## - O
            target_timestamp_O = np.array(routing_result_O[idx]['timestamp'])
            revision_timestamp_O = ((target_timestamp_O / max(target_timestamp_O)) * eta_result_O[idx]).tolist()

            routing_result_O[idx]['timestamp'] = revision_timestamp_O

            ## - D
            target_timestamp_D = np.array(routing_result_D[idx]['timestamp'])
            revision_timestamp_D = ((target_timestamp_D / max(target_timestamp_D)) * eta_result_D[idx]).tolist()

            routing_result_D[idx]['timestamp'] = revision_timestamp_D


    # *add_board_time 
    for idx in range(len(routing_result_D)):
        routing_result_D[idx]['timestamp'] = (np.array(routing_result_D[idx]['timestamp']) + simul_configs['add_board_time']).tolist()
    
    # 2. P_disembark_time D 마지막 시간으로 변경
    current_active_vehicle['P_disembark_time'] = [time+o['timestamp'][-1]+d['timestamp'][-1] for o,d in zip(routing_result_O, routing_result_D)]
    # *add_disembark_time 
    current_active_vehicle['P_disembark_time'] = current_active_vehicle['P_disembark_time'] + simul_configs['add_disembark_time']
    
    # 3. vehicle marker 저장
    vehicle_marker_inf = current_active_vehicle.loc[current_active_vehicle['temporary_stopTime'] != time]
    vehicle_marker_inf = vehicle_marker_inf.loc[~(vehicle_marker_inf['temporary_stopTime'].isna())].reset_index(drop=True)
    if len(vehicle_marker_inf) >= 1:
        vehicle_marker_inf = [{'vehicle_id':row['vehicle_id'], 
                               'cartype':row['cartype'],
                               'location': [row['lon'], row['lat']], 
                               'timestamp':[row['temporary_stopTime'], time]}\
                                    for _, row in vehicle_marker_inf.iterrows()]

        save_json_data(vehicle_marker_inf, save_path=save_path, file_name='vehicle_marker')
    del vehicle_marker_inf

    # 4. passenger marker 저장
    passenger_marker_inf = current_active_vehicle[['P_ID', 'P_ride_lat', 'P_ride_lon', 'P_request_time']]
    passenger_marker_inf['P_ride_time'] = [o['timestamp'][-1]+time for o in routing_result_O]
    
    if len(passenger_marker_inf) >= 1:

        passenger_marker_inf = [{'passenger_id':row['P_ID'], 'status':1,
                                'location': [row['P_ride_lon'], row['P_ride_lat']],
                                'timestamp':[row['P_request_time'], row['P_ride_time']]}\
                                    for _, row in passenger_marker_inf.iterrows()]

        save_json_data(passenger_marker_inf, save_path=save_path, file_name='passenger_marker')
    del passenger_marker_inf

    # 5. trip 저장
    O_route = [o['route'] for o in routing_result_O]
    D_route = [d['route'] for d in routing_result_D]
    O_timestamp =[list(np.array(o['timestamp'])+time) for o in routing_result_O]
    D_timestamp = [list(np.array(d['timestamp'])+o_timestamp[-1]) for d, o_timestamp in zip(routing_result_D, O_timestamp)]

    trip_inf = current_active_vehicle[['vehicle_id', 'P_ID' , 'cartype']]
    trip_inf['O_route'] = O_route
    trip_inf['D_route'] = D_route
    trip_inf['O_timestamp'] = O_timestamp
    trip_inf['D_timestamp'] = D_timestamp


    trip_inf_O = [{'vehicle_id':row['vehicle_id'], 'cartype':row['cartype'], 
                   'passenger_id':row['P_ID'], 'board':0,
                   'trip': row['O_route'], 'timestamp': row['O_timestamp']}\
                                for _, row in trip_inf.iterrows()]
    trip_inf_D = [{'vehicle_id':row['vehicle_id'], 'cartype':row['cartype'],
                   'passenger_id':row['P_ID'], 'board':1,
                   'trip': row['D_route'], 'timestamp': row['D_timestamp']}\
                                for _, row in trip_inf.iterrows()]

    trip_inf = []
    trip_inf.extend(trip_inf_O)
    trip_inf.extend(trip_inf_D)

    save_json_data(trip_inf, save_path=save_path, file_name='trip')
    del trip_inf
    del trip_inf_O
    del trip_inf_D
    
    return current_active_vehicle

## dispatch 방법 및 cost matrix 계산 방법 결정
from module.dispatch_cost import dispatch_cost_matrix
from module.dispatch import in_order_dispatch, ortools_dispatch

def dispatch_methods(requested_passenger, empty_vehicle, simul_configs, time):
    if simul_configs['dispatch_mode'] == 'optimization':
        cost_matrix = dispatch_cost_matrix(requested_passenger, 
                                           empty_vehicle, 
                                           time,
                                           simul_configs)
        
        
        dispatch_result = ortools_dispatch(requested_passenger, empty_vehicle, cost_matrix)
        del cost_matrix
        
    elif simul_configs['dispatch_mode'] == 'in_order':
        dispatch_result = in_order_dispatch(requested_passenger, 
                                            empty_vehicle,
                                            time,
                                            simul_configs)

    ## Matching complete
    # - dispatch 성공 차량 & 승객
    # - 승객 괜찮은데, 차량은 계속 차량 타입 가지고 가야됨!! (추후 수정)

    dispatch_result_vehicle = empty_vehicle.iloc[dispatch_result['vehicle']][['vehicle_id', 'cartype', 'work_end', 'temporary_stopTime', 'lat', 'lon']].reset_index(drop=True)
    dispatch_result_passenger = requested_passenger.iloc[dispatch_result['passenger']][['ID', 'ride_lat', 'ride_lon', 'alight_lat', 'alight_lon', 'ride_time', 'dispatch_time']].reset_index(drop=True)

    # - dispatch 성공 데이터 하나로 합침
    current_active_vehicle = pd.concat([dispatch_result_vehicle, dispatch_result_passenger], axis=1)
    current_active_vehicle = current_active_vehicle.rename(columns={'ID':'P_ID', 
                                                                    'ride_lat':'P_ride_lat',
                                                                    'ride_lon':'P_ride_lon',
                                                                    'alight_lat':'P_alight_lat', 
                                                                    'alight_lon':'P_alight_lon', 
                                                                    'ride_time':'P_request_time'})
    current_active_vehicle['P_disembark_time'] = 0

    ## Not match
    # - 남은 empty_vehicle, requested_passenger
    empty_vehicle = empty_vehicle.iloc[list(set(empty_vehicle.index)-set(dispatch_result['vehicle']))].reset_index(drop=True)
    requested_passenger = requested_passenger.iloc[list(set(requested_passenger.index)-set(dispatch_result['passenger']))].reset_index(drop=True)

    return requested_passenger, empty_vehicle, current_active_vehicle        


''''''
import pandas as pd
def part_of_dispatch_main(requested_passenger, active_vehicle, empty_vehicle, simul_configs, time):
    
    save_path = simul_configs['save_path']    
    
    check_variable = True
    
    ## 휠체어 승객 우선 배차를 위해 A(휠체어O), B(휠체어X)로 데이터 분리 
    # - 휠체어 우선 배차                                            

    requested_passenger = requested_passenger.reset_index(drop=True)
    empty_vehicle = empty_vehicle.reset_index(drop=True)

    A_requested_passenger = requested_passenger.loc[(requested_passenger['type'] == 1)].reset_index(drop=True)
    B_requested_passenger = requested_passenger.loc[(requested_passenger['type'] == 0)].reset_index(drop=True)

    A_empty_vehicle = empty_vehicle.loc[(empty_vehicle['cartype'] == 1)].reset_index(drop=True)
    B_empty_vehicle = empty_vehicle.loc[(empty_vehicle['cartype'] == 0)].reset_index(drop=True)

    if (len(A_requested_passenger) > 0) & (len(A_empty_vehicle) > 0):

        A_requested_passenger, A_empty_vehicle, A_current_active_vehicle = dispatch_methods(A_requested_passenger, A_empty_vehicle, simul_configs, time)

        empty_vehicle = pd.concat([A_empty_vehicle, B_empty_vehicle]).reset_index(drop=True)

        if (len(B_requested_passenger) > 0) & (len(empty_vehicle) > 0):

            B_requested_passenger, empty_vehicle, B_current_active_vehicle = dispatch_methods(B_requested_passenger, empty_vehicle, simul_configs, time)

            requested_passenger = pd.concat([A_requested_passenger, B_requested_passenger]).reset_index(drop=True)

            current_active_vehicle =  pd.concat([A_current_active_vehicle, B_current_active_vehicle]).reset_index(drop=True)
        else:
            requested_passenger = pd.concat([A_requested_passenger, B_requested_passenger]).reset_index(drop=True)

            current_active_vehicle = A_current_active_vehicle
            
    elif (len(B_requested_passenger) > 0) & (len(empty_vehicle) > 0):
        B_requested_passenger, empty_vehicle, current_active_vehicle = dispatch_methods(B_requested_passenger, empty_vehicle, simul_configs, time)

        requested_passenger = pd.concat([A_requested_passenger, B_requested_passenger]).reset_index(drop=True)
    else:
        check_variable = False

    ## 현재 시간에 활성화된 데이터 trip, point 저장 후 => current_active_vehicle 데이터로 반환
    if check_variable:
        if len(current_active_vehicle) >= 1:
            current_active_vehicle = address_current_active_vehicle(current_active_vehicle, time, save_path, simul_configs)
            active_vehicle = pd.concat([active_vehicle, current_active_vehicle])\

    active_vehicle = active_vehicle.reset_index(drop=True)    
    
    return requested_passenger, active_vehicle, empty_vehicle

def dispatch_main(requested_passenger, active_vehicle, empty_vehicle, simul_configs, time):

    if len(set(requested_passenger['dispatch_time'])) == 1:
        requested_passenger, active_vehicle, empty_vehicle = part_of_dispatch_main(requested_passenger, active_vehicle, empty_vehicle, simul_configs, time)
    else:
        row_lst = []
        for _, row in requested_passenger.groupby('dispatch_time'):
            row, active_vehicle, empty_vehicle = part_of_dispatch_main(row, active_vehicle, empty_vehicle, simul_configs, time)
            row_lst.append(row)
        requested_passenger = pd.concat(row_lst).reset_index(drop=True)
        
    return requested_passenger, active_vehicle, empty_vehicle
