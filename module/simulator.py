from .simulator_helper import *
from .simulator_object_update import *
import pandas as pd 
from tqdm import tqdm

class Simulator:
    
    def __init__(self, raw_data=None, passengers=None, vehicles=None, configs=None):
        
        # base configsation
        self.configs = configs    
        if self.configs == None:
            assert False, "Please input the configs data"

        # problem selector (helper function)
        self.extract_main = extract_selector(self.configs["problem"])
        self.dispatch_main = dispatch_selector(self.configs["problem"])

        # specify save paths (helper function)
        path_to_save_data = generate_path_to_save(self.configs['path'], self.configs['additional_path'])
        self.configs['save_path'] = path_to_save_data

        # object data (raw_data | passengers, vehicles)
        self.raw_data = raw_data
        self.passengers = passengers
        self.vehicles = vehicles

        if self.raw_data != None:            
            self.passengers, self.vehicles, YMD = self.extract_main(self.raw_data, self.configs)
            self.configs['YMD'] = YMD
        else:
            self.configs['YMD'] = pd.Timestamp('2019-04-09 00:00:00')
        
        # data preprocessing (helper function)
        self.passengers, self.vehicles = crop_data_by_timerange(self.passengers, self.vehicles, self.configs)
            
        # generate simulation base-data   
        self.active_vehicle, self.empty_vehicle, self.requested_passenger, self.fail_passenger, self.simulation_record =\
            base_data()
              
    ### Generate simulation base-data
    def base_data():
        active_vehicle, empty_vehicle, requested_passenger, fail_passenger =\
            pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        simulation_record = pd.DataFrame(columns=['time',
                                                  'waiting_passenger_cnt',
                                                  'fail_passenger_cnt',
                                                  'empty_vehicle_cnt',
                                                  'driving_vehicle_cnt'])
        return active_vehicle, empty_vehicle, requested_passenger, fail_passenger, simulation_record

    ### simulation run function
    def run(self):
        start_time, end_time = self.configs['time_range'][0], self.configs['time_range'][1]
        
        for time in tqdm(range(start_time, end_time)):
            ### Update passenger & vehicle
            # - passenger
            self.requested_passenger, self.fail_passenger, self.passengers = update_passenger(self.requested_passenger, 
                                                                                              self.fail_passenger,  
                                                                                              self.passengers, 
                                                                                              self.configs,
                                                                                              time)
            
            # - vehicle
            self.active_vehicle, self.empty_vehicle, self.vehicles = update_vehicle(self.active_vehicle,
                                                                                   self.empty_vehicle, 
                                                                                   self.vehicles,
                                                                                   self.configs,
                                                                                   time)
            
            ### Dispatch (matching passenger and vehicle)     
            if (len(self.requested_passenger) > 0) & (len(self.empty_vehicle) > 0):
                self.requested_passenger, self.active_vehicle, self.empty_vehicle = self.dispatch_main(self.requested_passenger, 
                                                                                                       self.active_vehicle, 
                                                                                                       self.empty_vehicle, 
                                                                                                       self.configs, 
                                                                                                       time)

            ### Simulation progress check function 
            # - record the current status (number of requested_passenger, fail_passenger, empty_vehicle, active_vehicle)
            self.simulation_record = checking_progress(self.simulation_record, time, self.requested_passenger, self.fail_passenger, self.empty_vehicle, self.active_vehicle, self.configs)
