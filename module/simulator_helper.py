### extract, dispatch function selector
# - extract_selector
def extract_selector(service_type):
    service_type = service_type.upper()
    
    if service_type == 'DISABLEDCALLTAXI':
        from .services.disabled_callTaxi.extract_data import extract_main
        return extract_main
        
# - dispatch_selector
def dispatch_selector(service_type):
    service_type = service_type.upper()

    if service_type == 'DISABLEDCALLTAXI':
        from .services.disabled_callTaxi.dispatch_flow import dispatch_main
        return dispatch_main  
    
### Generate path to save 
import os
def generate_path_to_save(result_folder_name = None, additional_path=None):
    # base path
    base_path = os.path.join(os.getcwd(), "simul_result") 
    if not(os.path.isdir(base_path)):
        os.mkdir(base_path)
        
    # base path + additional_path
    if additional_path != None:
        base_path = os.path.join(base_path, additional_path)
        if not(os.path.isdir(base_path)):
            os.mkdir(base_path)
    
    # folder to save simulation result  
    if result_folder_name != None:
        if not(result_folder_name in os.listdir(base_path)):
            base_path = os.path.join(base_path, result_folder_name)
            os.mkdir(base_path)
        else:
            result_folder_name = f"simulation_{len(os.listdir(base_path)) + 1}"
            base_path = os.path.join(base_path, result_folder_name)
            os.mkdir(base_path)
    else:
        result_folder_name = f"simulation_{len(os.listdir(base_path)) + 1}"
        base_path = os.path.join(base_path, result_folder_name)
        os.mkdir(base_path)
        
    return base_path

### Save json data 
import json
def save_json_data(current_data, save_path, file_name):
    
    if os.path.isfile(f'{save_path}/{file_name}.json'): 
        with open(f'{save_path}/{file_name}.json', 'r') as f:
            prior_data = json.load(f)
        
        prior_data.extend(current_data)
        
        with open(f'{save_path}/{file_name}.json', 'w') as f:
            json.dump(prior_data, f)
    else:
        with open(f'{save_path}/{file_name}.json', 'w') as f:
            json.dump(current_data, f)    
    
    
### Preprocessing passengers, vehicles data
def crop_data_by_timerange(passengers, vehicles, inform):
    start_time, end_time = inform['time_range']
    
    # - passenger
    passengers = passengers.loc[(passengers['ride_time'] >= start_time) & (passengers['ride_time'] < end_time)]
    passengers = passengers.reset_index(drop=True)
    # - vehicle
    vehicles = vehicles.loc[(vehicles['work_end'] > start_time)]
    vehicles.loc[(vehicles['work_start']) < start_time, 'work_start'] = start_time
    vehicles.loc[(vehicles['work_end'] > inform['time_range'][-1]), 'work_end'] = inform['time_range'][-1]
    vehicles = vehicles.reset_index(drop=True)
    
    return passengers, vehicles

### Simulation progress check function
import pandas as pd 
import matplotlib.pyplot as plt
from IPython.display import clear_output

def checking_progress(simulation_record, current_time, requested_passenger, fail_passenger, empty_vehicle, active_vehicle, inform):

    time_range = inform['time_range']
    save_path = inform['save_path']

    current_record = pd.DataFrame({
        'time' : [current_time],
        'waiting_passenger_cnt' : [len(requested_passenger)],
        'fail_passenger_cnt' : [len(fail_passenger)],
        'empty_vehicle_cnt' : [len(empty_vehicle)],
        'driving_vehicle_cnt' : [len(active_vehicle)]
        })

    simulation_record = pd.concat([simulation_record, current_record]).reset_index(drop=True)

    # simulation operation graph
    clear_output(True)
    plt.figure(figsize=(18, 10))
    plt.rcParams['axes.grid'] = True 
    plt.plot(simulation_record['time'].values, simulation_record['waiting_passenger_cnt'].values, label = f"waiting passengers ({len(requested_passenger)})", color='royalblue')
    plt.plot(simulation_record['time'].values, simulation_record['empty_vehicle_cnt'].values, label = f"Idle vehicles ({len(empty_vehicle)})", color= 'darkorange')
    plt.plot(simulation_record['time'].values, simulation_record['driving_vehicle_cnt'].values, label = f"In-service vehicles ({len(active_vehicle)})", color= 'limegreen')
    plt.legend()
    plt.show()

    # save simulation record 
    if current_time == (time_range[-1]-1):
        simulation_record.to_csv(f'{save_path}/record.csv', index=False)
    
    return simulation_record
        
### Generate simulation base-data
# import pandas as pd 
def base_data():
    active_vehicle, empty_vehicle, requested_passenger, fail_passenger =\
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    simulation_record = pd.DataFrame(columns=['time',
                                              'waiting_passenger_cnt',
                                              'fail_passenger_cnt', 
                                              'empty_vehicle_cnt',
                                              'driving_vehicle_cnt', 
                                              'iter_time(second)'])
    
    return active_vehicle, empty_vehicle, requested_passenger, fail_passenger, simulation_record


### 시뮬레이션 시작 전 데이터 전처리
def seoul_passenger_preprocessing(passengers):
    passengers = passengers[['ID', 'ride_time', 'ride_lat', 'ride_lon', 'alight_lat', 'alight_lon', 'dispatch_time', 'type']]
    return passengers

def seoul_vehicle_preprocessing(vehicles):
    vehicles = vehicles[['vehicle_id', 'cartype', 'work_start', 'work_end', 'temporary_stopTime', 'lat', 'lon']]
    vehicles['work_start'] = vehicles['work_start'] * 60
    vehicles['work_end'] = vehicles['work_end'] * 60
    return vehicles

def get_preprocessed_seoul_data(passengers, vehicles):
    passengers = seoul_passenger_preprocessing(passengers)
    vehicles = seoul_vehicle_preprocessing(vehicles)
    return passengers, vehicles


### base configs
base_configs = {'target_region': '서울 대한민국',
                  'problem': 'disabledCalltaxi',
                  'relocation_region': 'seoul',
                  'path': None, # simul_result에 원하는 path 그 자리에 생김
                  'additional_path':None, # simul_result에 이 자리위에 생김
                  'time_range':[360, 1440],
                  'fail_time': 30,
                  'add_board_time': 10,
                  'add_disembark_time': 10,
                  'matrix_mode': 'street_distance', # ['street_distance', 'ETA', 'haversine_distance']
                  'dispatch_mode': 'in_order', # ['optimization', 'in_order']
                  'eta_model': None,
                  'view_operation_graph':True}



### simulation "result.json" 만드는 코드
import os
import pandas as pd
import numpy as np

def generate_simulation_result_json(passengers, trip, records, time_range=[360, 1440]):
    trip['start_time'] = [ts[0] for ts in trip['timestamp']]
    trip['end_time'] = [ts[-1] for ts in trip['timestamp']]

    passengers['start_time'] = [ts[0] for ts in passengers['timestamp']]
    passengers['end_time'] = [ts[-1] for ts in passengers['timestamp']]

    driving_vehicle_num_lst = []
    dispatched_vehicle_num_lst = []
    occupied_vehicle_num_lst = []
    empty_vehicle_num_lst = []
    fail_passenger_cumNum_lst = []
    waiting_passenger_num_lst = []
    average_waiting_time_lst = []
    current_waiting_time_dict_lst = []
    for tm in range(time_range[0], time_range[1]):
        current_record = records.loc[(records['time'] == tm )].reset_index(drop=True)
        total_vehicle_num = current_record['empty_vehicle_cnt'].iloc[0] + current_record['driving_vehicle_cnt'].iloc[0]
        empty_vehicle_num = current_record['empty_vehicle_cnt'].iloc[0] 

        operating_vehicle = trip.loc[((trip['start_time'] <= tm) & (trip['end_time'] >= tm))].reset_index(drop=True).drop_duplicates('vehicle_id')
        dispatched_vehicle = operating_vehicle.loc[(operating_vehicle['board'] == 0)].reset_index(drop=True)
        occupied_vehicle = operating_vehicle.loc[(operating_vehicle['board'] == 1)].reset_index(drop=True)

        ### vehicle num        
        driving_vehicle_num = len(operating_vehicle)
        dispatched_vehicle_num = len(dispatched_vehicle)
        occupied_vehicle_num = len(occupied_vehicle)
        
        driving_vehicle_num_lst.append(driving_vehicle_num)
        dispatched_vehicle_num_lst.append(dispatched_vehicle_num)
        occupied_vehicle_num_lst.append(occupied_vehicle_num)
        empty_vehicle_num_lst.append(empty_vehicle_num)
        
        ### passenger num
        fail_passenger_cumNum = current_record['fail_passenger_cnt'].iloc[0]    
     
        # "waiting_passenger_num", "average_waiting_time", "current_waiting_time_dict"
        waiting_passengers = passengers.loc[(passengers['start_time'] <= tm) & (passengers['end_time'] >= tm)].reset_index(drop=True)
        waiting_passenger_num = len(waiting_passengers)
        
        waiting_passengers['wait_time'] = tm - waiting_passengers['start_time']
        average_waiting_time = np.mean(waiting_passengers['wait_time'])
        
        waiting_passengers['wait_time_cate'] = pd.cut(waiting_passengers['wait_time'],
                                                bins=[0, 10, 20, 30, 40, 50, np.inf],
                                                labels=[0,10,20,30,40,50],
                                                right=False)
        waiting_time_dictionary= round(waiting_passengers['wait_time_cate'].value_counts(normalize=True) * 100, 2).to_dict()
        current_waiting_time_dict = {}
        for k, v in zip(waiting_time_dictionary.keys(), waiting_time_dictionary.values()):
            current_waiting_time_dict[str(k)] = v
            
        fail_passenger_cumNum_lst.append(fail_passenger_cumNum)
        waiting_passenger_num_lst.append(waiting_passenger_num)
        average_waiting_time_lst.append(average_waiting_time)
        current_waiting_time_dict_lst.append(current_waiting_time_dict)
        
    results = pd.DataFrame({'time': range(time_range[0], time_range[1]),
                'driving_vehicle_num': driving_vehicle_num_lst,
                'dispatched_vehicle_num': dispatched_vehicle_num_lst,
                'occupied_vehicle_num': occupied_vehicle_num_lst,
                'empty_vehicle_num': empty_vehicle_num_lst,
                'fail_passenger_cumNum': fail_passenger_cumNum_lst,
                'waiting_passenger_num': waiting_passenger_num_lst,
                'average_waiting_time': average_waiting_time_lst,
                'current_waiting_time_dict': current_waiting_time_dict_lst})
    
    results['average_waiting_time'] = round(results['average_waiting_time'], 1) 
    return results