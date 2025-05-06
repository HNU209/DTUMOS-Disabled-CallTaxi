from .simulator_helper import save_json_data
import pandas as pd
import numpy as np 


###########################
# Passenger status update #
###########################
# - 1. passenger에서 활성(요청) 필요 데이터 추출
# - 2. passenger 설정된 fail_time 만큼 되면 실패 상태로 전환 or 넘지 않으면 dispatch_time +1
def update_passenger(requested_passenger, fail_passenger, passenger, simul_configs, time):
    
    fail_time = simul_configs['fail_time']
    save_path = simul_configs['save_path']
    
    current_requested_passenger = passenger.loc[(passenger['ride_time'] == time)]
    passenger = passenger.loc[(passenger['ride_time'] != time)]
    passenger = passenger.reset_index(drop=True)
    
    if len(requested_passenger) > 0:
        
        requested_passenger['dispatch_time'] = requested_passenger['dispatch_time'] + 1
        
        current_fail_passenger = requested_passenger.loc[(requested_passenger['dispatch_time'] >= fail_time)]
        fail_passenger= pd.concat([fail_passenger, current_fail_passenger])
        fail_passenger = fail_passenger.reset_index(drop=True)
        
        if len(current_fail_passenger) > 0:             
            
            requested_passenger = requested_passenger.loc[(requested_passenger['dispatch_time'] < fail_time)]
            
            current_fail_passenger = [{'passenger_id':row['ID'], 'status':0,
                                       'location': [row['ride_lon'], row['ride_lat']], 
                                       'timestamp':[row['ride_time'], row['ride_time'] + row['dispatch_time']]}\
                                           for _, row in current_fail_passenger.iterrows()]            
            
            save_json_data(current_fail_passenger, save_path, file_name='passenger_marker')
            del current_fail_passenger
    
    
    requested_passenger = pd.concat([requested_passenger, current_requested_passenger])
    requested_passenger = requested_passenger.reset_index(drop=True)
    
    return requested_passenger, fail_passenger, passenger

#########################
# Vehicle status update #
#########################
# active_vehicle, empty_vehicle columns : ['vehicle_id', 'work_end', 'temporary_stopTime', 'geometry', 'P_ID', 'P_ride_geometry', 'P_alight_geometry', 'P_disembark_time']
# - 1. 출근 차량 체크
# - 2. 운행 중인 차량 승객 하차 체크 
# - 3. 퇴근 차량 체크
def update_vehicle(active_vehicle, empty_vehicle, vehicle, simul_configs, time):
    
    save_path = simul_configs['save_path']
    
    # 출근 체크
    current_start_vehicle = vehicle.loc[(vehicle['work_start'] == time)]
    
    if len(current_start_vehicle) > 0:
        
        if 'cartype' in current_start_vehicle.columns:
            current_start_vehicle = current_start_vehicle[['vehicle_id', 'cartype', 'work_end', 'temporary_stopTime', 'lat', 'lon']]
        else:
            current_start_vehicle = current_start_vehicle[['vehicle_id', 'work_end', 'temporary_stopTime', 'lat', 'lon']]
        
        current_start_vehicle['temporary_stopTime'] = time
        current_start_vehicle['P_ID'] = np.nan
        current_start_vehicle['P_ride_lat'] = np.nan
        current_start_vehicle['P_ride_lon'] = np.nan
        current_start_vehicle['P_alight_lat'] = np.nan
        current_start_vehicle['P_alight_lon'] = np.nan
        current_start_vehicle['P_request_time'] = np.nan
        current_start_vehicle['P_disembark_time'] = np.nan
        
        empty_vehicle = pd.concat([empty_vehicle, current_start_vehicle])
        empty_vehicle = empty_vehicle.reset_index(drop=True)
        
        vehicle = vehicle.loc[(vehicle['work_start'] != time)]
        vehicle = vehicle.reset_index(drop=True)
        
    # 승객 내림 체크
    if len(active_vehicle) > 0:
        
        current_empty_vehicle = active_vehicle.loc[(active_vehicle['P_disembark_time'] <= time)].copy()
        
        if len(current_empty_vehicle) > 0:
            # 현재 승객 내린 차량 update
            current_empty_vehicle['lat'] = current_empty_vehicle['P_alight_lat']
            current_empty_vehicle['lon'] = current_empty_vehicle['P_alight_lon']
            current_empty_vehicle['temporary_stopTime'] = current_empty_vehicle['P_disembark_time']
            
            current_empty_vehicle['P_ID'] = np.nan
            current_empty_vehicle['P_ride_lat'] = np.nan
            current_empty_vehicle['P_ride_lon'] = np.nan
            current_empty_vehicle['P_alight_lat'] = np.nan
            current_empty_vehicle['P_alight_lon'] = np.nan
            current_empty_vehicle['P_disembark_time'] = np.nan
        
            empty_vehicle = pd.concat([empty_vehicle, current_empty_vehicle])
            empty_vehicle = empty_vehicle.reset_index(drop=True)
            
            # 아직 운행 중인 차량 update
            active_vehicle = active_vehicle.loc[(active_vehicle['P_disembark_time'] > time)]
            active_vehicle = active_vehicle.reset_index(drop=True)
            
    # 퇴근 체크
    if len(empty_vehicle) > 0: 
        
        end_vehicle = empty_vehicle.loc[(empty_vehicle['work_end'] < time+5)] 
        end_vehicle = end_vehicle.loc[(end_vehicle['temporary_stopTime'] != time)]        
    
        empty_vehicle = empty_vehicle.loc[(empty_vehicle['work_end'] >= time+5)]   
        empty_vehicle = empty_vehicle.reset_index(drop=True)
        
        if len(end_vehicle) > 0:
            
            # temporary_stopTime이 NaN인 경우는 퇴근 차량이지만 relocation을 하다가 바로 퇴근을 해서 vehicle marker가 필요 없는 경a우임 
            if 'cartype' in current_start_vehicle.columns:
                end_vehicle = [{'vehicle_id':row['vehicle_id'], 'cartype':row['cartype'],
                                'location': [row['lon'], row['lat']], 
                                'timestamp':[row['temporary_stopTime'], time]}\
                                    for _, row in end_vehicle.iterrows() if ~(np.isnan(row['temporary_stopTime']))]            
            else:
                end_vehicle = [{'vehicle_id':row['vehicle_id'],
                                'location': [row['lon'], row['lat']], 
                                'timestamp':[row['temporary_stopTime'], time]}\
                                    for _, row in end_vehicle.iterrows() if ~(np.isnan(row['temporary_stopTime']))]  
            
            save_json_data(end_vehicle, save_path, file_name='vehicle_marker')
            del end_vehicle
    
    return active_vehicle, empty_vehicle, vehicle