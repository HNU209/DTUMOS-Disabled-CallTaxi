dashboard_config = {
    # path
    'base_path':'./result/baseline/', 
    'save_figure_path': "./visualization/dashboard/assets/figure/",
    'save_file_path': "./visualization/dashboard/assets/data/",
    'region_boundary_file_path': 'C:/Users/yh_zoo/Desktop/___disabled calltaxi DTUMOS/data/etc/HangJeongDong_ver20230701.geojson',
    # time range
    'time_range' : [360, 1440],
    # target region
    'target_region_name' : '서울특별시',
    # mapboxkey
    'mapboxKey' : "pk.eyJ1Ijoic3BlYXI1MzA2IiwiYSI6ImNremN5Z2FrOTI0ZGgycm45Mzh3dDV6OWQifQ.kXGWHPRjnVAEHgVgLzXn2g",
}

import os 
import osmnx as ox
import numpy as np
import pandas as pd
import geopandas as gpd

'''level_of_service'''
# import numpy as np 
from .figures.level_of_service import figure_1, figure_2, figure_3
def figures_Of_level_of_service(base_path, save_path, time_range):
    # Time variables
    time_bins = [tm for tm in range(time_range[0], time_range[1], 60)]
    time_bins.append(np.inf)
    time_single_labels = [str(int(tm/60)).zfill(2) + ":00" for tm in range(time_range[0], time_range[1], 60)]
    time_double_labels = [str(int(tm/60)).zfill(2) + '-' + str(int(tm/60)+1).zfill(2) for tm in range(time_range[0], time_range[1], 60)]

    # Figures
    figure_1(base_path, time_range=time_range, time_bins=time_bins, time_single_labels=time_single_labels, save_path = save_path)
    figure_2(base_path, time_bins=time_bins, time_single_labels=time_single_labels, time_double_labels=time_double_labels, save_path = save_path)
    figure_3(base_path, time_range=time_range, time_bins=time_bins, time_single_labels=time_single_labels, save_path = save_path)

'''vehicle_operation_status'''
# import numpy as np 
from .figures.vehicle_operation_status import figure_4, figure_5
def figures_Of_vehicle_operation_status(base_path, save_path, time_range):
    # Time variables
    time_bins = [tm for tm in range(time_range[0], time_range[1], 60)]
    time_bins.append(np.inf)
    time_single_labels = [str(int(tm/60)).zfill(2) + ":00" for tm in range(time_range[0], time_range[1], 60)]

    # Figures
    figure_4(base_path, time_range=time_range, time_single_labels=time_single_labels, save_path = save_path)
    figure_5(base_path, time_bins=time_bins, time_single_labels=time_single_labels, save_path = save_path)
    
'''spatial_distribution'''
# import osmnx as ox
# import numpy as np
# import geopandas as gpd
from .figures.spatial_distribution import figure_6_7_N_8_9, figure_10, figure_11
def figures_Of_spatial_distribution(base_path, save_path, region_boundary_file_path, time_range, target_region_name, mapboxKey):
    # Geometry
    place_geometry = ox.geocode_to_gdf([target_region_name])
    region_boundary = gpd.read_file(region_boundary_file_path)
    region_boundary = region_boundary.loc[(region_boundary['sidonm'] == target_region_name)].reset_index(drop=True)

    # Figures
    figure_6_7_N_8_9(base_path, place_geometry, mapboxKey = mapboxKey, time_range=time_range, status='pickup', save_path = save_path)
    figure_6_7_N_8_9(base_path, place_geometry, mapboxKey = mapboxKey, time_range=time_range, status='dropoff', save_path = save_path)
    figure_10(base_path, place_geometry, region_boundary, mapboxKey = mapboxKey, save_path = save_path)
    figure_11(base_path, place_geometry, region_boundary, mapboxKey = mapboxKey, save_path = save_path)
    
    
'''simulation_configurations'''
def simulation_configuration_for_dashboard(base_path, save_path):
    simul_result_inf = {
        'total_calls': [],
        'failed_calls':[],
        'failure_rate':[],
        'vehicles_driven':[]
    }
    for fd_nm in os.listdir(base_path):    
        passengers = pd.read_json(base_path + fd_nm + '/passenger_marker.json')
        passenger_number = len(set(passengers['passenger_id']))
        simul_result_inf['total_calls'].append(passenger_number)
        
        records = pd.read_csv(base_path + fd_nm + '/record.csv')
        records['operating_vehicle_cnt'] = records['empty_vehicle_cnt'] + records['driving_vehicle_cnt']
        failed_calls_num = records['fail_passenger_cnt'].iloc[-1]
        failure_rate = round((failed_calls_num / passenger_number) * 100, 2)    
        simul_result_inf['failed_calls'].append(failed_calls_num)
        simul_result_inf['failure_rate'].append(failure_rate)
        
        vehicles = pd.read_json(base_path + fd_nm + '/vehicle_marker.json')
        vehicle_id_1 = set(vehicles['vehicle_id'])
        trips = pd.read_json(base_path + fd_nm + '/trip.json')
        vehicle_id_2 = set(trips['vehicle_id'])
        vehicle_driven_num = len(vehicle_id_1 & vehicle_id_2)
        simul_result_inf['vehicles_driven'].append(vehicle_driven_num)

    simul_result_inf = pd.DataFrame(simul_result_inf)
    simul_result_inf = pd.DataFrame(simul_result_inf.mean()).T

    simul_result_inf[['total_calls', 'failed_calls', 'vehicles_driven']] = simul_result_inf[['total_calls', 'failed_calls', 'vehicles_driven']].astype(int)
    simul_result_inf['failure_rate'] = round(simul_result_inf['failure_rate'], 2)

    if save_path != None:
        simul_result_inf.to_csv(f'{save_path}stats.csv', sep=',',index=False)
    else: 
        return simul_result_inf
    
# MAIN - generate everthing about dashboard
def generate_dashboard_materials(dashboard_config):
    simulation_configuration_for_dashboard(dashboard_config['base_path'], dashboard_config['save_file_path'])

    figures_Of_level_of_service(dashboard_config['base_path'], dashboard_config['save_figure_path'],
                                dashboard_config['time_range'])
    figures_Of_vehicle_operation_status(dashboard_config['base_path'], dashboard_config['save_figure_path'],
                                        dashboard_config['time_range'])
    figures_Of_spatial_distribution(dashboard_config['base_path'], dashboard_config['save_figure_path'], dashboard_config['region_boundary_file_path'], 
                                    dashboard_config['time_range'],
                                    dashboard_config['target_region_name'], dashboard_config['mapboxKey'])