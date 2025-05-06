import sys
sys.path.append("..")
###
from module.point_generator import point_generator_with_OSM
import pandas as pd 
import numpy as np 
import copy 
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

#########################
# Convert time-standard #
#########################
# - This time-standard of simulation is based on minutes except for YMD(Year-Month-date)
# - HOUR:MINUTE:SECOND -> Minute

def convert_time_standard(operation_record):
    operation_record['ride_time'] = pd.to_datetime(operation_record['ride_time'])

    YMD = list(set(operation_record['ride_time'].dt.strftime('%Y%m%d')))

    target_YMD = min([datetime.strptime(i,'%Y%m%d') for i in YMD])   

    operation_record['ride_time'] = operation_record['ride_time'] - target_YMD
    operation_record['ride_time'] = operation_record['ride_time']/pd.Timedelta(minutes=1)
    operation_record['ride_time'] = np.floor(operation_record['ride_time']).astype('int')
    
    return operation_record, target_YMD


#####################
# Extract Passenger #
#####################
# - 특징은 승객 휠체어 이용 여부를 알 수 없기 때문에 비율 고려하여, 승객 타입 부여
# - columns : ['ID', 'ride_time', 'ride_geometry', 'alight_geometry', 'dispatch_time', 'type']
def extract_passenger(operation_record, simulation_inf):
    
    # 승객 수 변화 없음
    if not('passenger_increase_ratio' in simulation_inf.keys()):
        # taxi_operation_record로 승객 데이터 추출
        passenger = operation_record[['ride_time', 'ride_lat', 'ride_lon', 'alight_lat', 'alight_lon']]

        # 승객 ID 생성
        passenger = passenger.reset_index(drop=False)
        passenger = passenger.rename(columns={'index': 'ID'})

        # 승객 dispatch_time 생성
        passenger['dispatch_time'] = 0 # dispatch_time이란 taxi를 잡기 전 까지 걸리는 시간!

        # 고객 type 부여 (0 : 휠체어 미이용, 1 : 휠체어 이용)
        type_list = np.random.choice(2 ,size = len(passenger), p=[0.23, 0.77]) ## 0(휠체어X): 23%, 1(휠체어O) : 77%
        passenger["type"] = type_list
        
        return passenger
    # 승객 수 (증가 / 감소)
    else:
        passenger = operation_record[['ride_time', 'ride_lat', 'ride_lon', 'alight_lat', 'alight_lon']]
        
        passenger_increase_ratio = simulation_inf['passenger_increase_ratio']
        
        if  passenger_increase_ratio <= 1:        
            passenger = passenger.sample(frac=passenger_increase_ratio).sort_values('ride_time').reset_index(drop=True).reset_index()
            passenger = passenger.rename(columns={'index': 'ID'})
            
            type_list = np.random.choice(2 ,size = len(passenger), p=[0.23, 0.77]) # 0(휠체어X): 23%, 1(휠체어O) : 77%
            passenger["type"] = type_list
        else:
            add_passenger = passenger.sample(frac=passenger_increase_ratio-1).copy()
            add_passenger = add_passenger.reset_index(drop=True)
            
            # 장소 기반 포인트 생성
            point_generator = point_generator_with_OSM()
            add_passenger_point = point_generator.point_generator_about_placeName(place=simulation_inf['target_region'], count=len(add_passenger) * 2)
            
            ride_point = add_passenger_point[:len(add_passenger)].reset_index(drop=True)
            alight_point = add_passenger_point[len(add_passenger):].reset_index(drop=True)
            
            add_passenger[['ride_lat', 'ride_lon']] = ride_point[['lat', 'lon']] 
            add_passenger[['alight_lat', 'alight_lon']] = alight_point[['lat', 'lon']]           
            
            passenger = pd.concat([passenger, add_passenger]).sort_values('ride_time').reset_index(drop=True).reset_index()
            passenger = passenger.rename(columns={'index': 'ID'})
            
            type_list = np.random.choice(2 ,size = len(passenger), p=[0.23, 0.77]) # 0(휠체어X): 23%, 1(휠체어O) : 77%
            passenger["type"] = type_list
        
        # 승객 dispatch_time 생성
        passenger['dispatch_time'] = 0 # dispatch_time이란 taxi를 잡기 전 까지 걸리는 시간!
        
        '''여기부터 수정'''
        # passenger column 순서 정렬
        passenger = passenger[['ID', 'ride_time', 'ride_lat', 'ride_lon', 'alight_lat', 'alight_lon', 'dispatch_time', 'type']]
    
        return passenger


################
# Extract Taxi #
################
# -'vehicle_id 별 최소 탑승 시간과 최대 하차 시간으로 taxi_schedule을 생성한다.
# - 주간근무자 17시 이전 근무자 9시간 근무
# - 야간근무자 17시 이후 근무자 12시간 근무 
def extract_taxi(operation_record, simulation_inf):
    
    if not('taxi_schedule' in simulation_inf.keys()):
        
        taxi_schedule_dict = dict()

        for id, row in operation_record.groupby('vehicle_id'):
            taxi_schedule_dict[id] = [row['cartype'].iloc[0], row['ride_time'].min(), row['ride_time'].max()]

        taxi_schedule = pd.DataFrame(taxi_schedule_dict).T.reset_index()
        taxi_schedule.columns = ['vehicle_id', 'cartype', 'work_start', 'work_end']

        taxi_schedule['temporary_stopTime'] = 0 

        ## taxi 운행표 생성
        bins = [i*60 for i in range(6,31)]
        labels = [i for i in range(6,30)]

        work_startTime = pd.cut(taxi_schedule['work_start'], bins=bins, labels=labels, right=False)
        taxi_schedule['work_start'] = work_startTime.tolist()

        ## 주간, 야간 근무자의 근무 시간이 다르기 때문에 근무 시간 아래와 같이 차별 부여 
        # - A조(주간근무자) 17시 이전 근무자 9시간 근무 : 06:00~17:00시
        # - B조(야간근무자) 17시 이후 근무자 12시간 근무 : 이외 시간
        A_group_timeTable = list(range(6,17))

        A_taxi_schedule = taxi_schedule.loc[(taxi_schedule['work_start'].isin(A_group_timeTable))]
        B_taxi_schedule = taxi_schedule.loc[~(taxi_schedule['work_start'].isin(A_group_timeTable))]

        A_taxi_schedule['work_end'] = A_taxi_schedule['work_start'] + 9
        B_taxi_schedule['work_end'] = B_taxi_schedule['work_start'] + 12

        taxi_schedule = pd.concat([A_taxi_schedule, B_taxi_schedule]).reset_index(drop=True)

        ## 시뮬레이션 시간 상 6~30시이기 때문에 30시 이후 운행 차량 데이터 조정 
        # - 예) 17시~31시 근무 차량 => 0~1시, 17~30시 근무로 변경
        taxi_inMorning = taxi_schedule.loc[(taxi_schedule['work_end'] <= 30)]
        taxi_inNight = taxi_schedule.loc[(taxi_schedule['work_end'] > 30)]

        over_time = taxi_inNight['work_end'] - 30
        taxi_inNight['work_end'] = 30

        taxi_inNight_copy = copy.deepcopy(taxi_inNight)
        taxi_inNight_copy['work_start'] = 0 
        taxi_inNight_copy['work_end'] = over_time

        taxi_inNight = pd.concat([taxi_inNight, taxi_inNight_copy])

        taxi_schedule = pd.concat([taxi_inMorning, taxi_inNight]).sort_values('work_start').reset_index(drop=True)

        taxi_schedule['work_start'] = taxi_schedule['work_start'] * 60
        taxi_schedule['work_end'] = taxi_schedule['work_end'] * 60


        point_generator = point_generator_with_OSM()
        taxi_point = point_generator.point_generator_about_placeName(place=simulation_inf['target_region'], count=len(taxi_schedule))
        taxi_schedule['lat'] = taxi_point['lat']
        taxi_schedule['lon'] = taxi_point['lon']
        
        return taxi_schedule
    else:
        ## 사용자가 생성한 시뮬레이션 데이터 사용
        taxi_schedule = simulation_inf['taxi_schedule']
        
        taxi_schedule['temporary_stopTime'] = 0

        point_generator = point_generator_with_OSM()
        taxi_point = point_generator.point_generator_about_placeName(place=simulation_inf['target_region'], count=len(taxi_schedule))
        taxi_schedule['lat'] = taxi_point['lat']
        taxi_schedule['lon'] = taxi_point['lon']        
        
        ## 시뮬레이션 시간 상 6~30시이기 때문에 30시 이후 운행 차량 데이터 조정 
        # - 예) 17시~31시 근무 차량 => 0~1시, 17~30시 근무로 변경
        taxi_inMorning = taxi_schedule.loc[(taxi_schedule['work_end'] <= 30)]
        taxi_inNight = taxi_schedule.loc[(taxi_schedule['work_end'] > 30)]

        over_time = taxi_inNight['work_end'] - 30
        taxi_inNight['work_end'] = 30

        taxi_inNight_copy = copy.deepcopy(taxi_inNight)
        taxi_inNight_copy['work_start'] = 0 
        taxi_inNight_copy['work_end'] = over_time

        taxi_inNight = pd.concat([taxi_inNight, taxi_inNight_copy])

        taxi_schedule = pd.concat([taxi_inMorning, taxi_inNight]).sort_values('work_start').reset_index(drop=True)

        taxi_schedule['work_start'] = taxi_schedule['work_start'] * 60
        taxi_schedule['work_end'] = taxi_schedule['work_end'] * 60
    
        return taxi_schedule


#####################
# Main data extract #
#####################
def extract_main(operation_record, simulation_inf):
    
    operation_record, YMD = convert_time_standard(operation_record)

    passenger = extract_passenger(operation_record, simulation_inf)

    taxi = extract_taxi(operation_record, simulation_inf) 
    
    return passenger, taxi, YMD