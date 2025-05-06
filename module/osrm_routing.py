# library
from .utils import calculate_straight_distance
import numpy as np
import itertools
import requests
import polyline
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import warnings 
warnings.filterwarnings('ignore')

#############
# OSRM base #
#############
def get_res(point):

   status = 'defined'

   session = requests.Session()
   # retry = Retry(connect=3, backoff_factor=0.5)
   retry = Retry(connect=10, backoff_factor=1)
   adapter = HTTPAdapter(max_retries=retry)
   session.mount('http://', adapter)
   session.mount('https://', adapter)

   overview = '?overview=full'
   loc = f"{point[1]},{point[0]};{point[3]},{point[2]}" # lon, lat, lon, lat
   url = "http://127.0.0.1:5000/route/v1/driving/"
   # url = 'http://router.project-osrm.org/route/v1/driving' # OSRM docker 없을때 사용
   r = session.get(url + loc + overview) 
   
   if r.status_code!= 200:
      
      status = 'undefined'
      
      # distance    
      distance = calculate_straight_distance(point[0], point[1], point[2], point[3]) * 1000
      
      # route
      route = [[point[1], point[0]], [point[3], point[2]]]

      # duration & timestamp
      speed_km = 10#km
      speed = (speed_km * 1000/60)      
      duration = distance/speed
      
      timestamp = [0, duration]
         
      result = {'route': route, 'timestamp': timestamp, 'duration': duration, 'distance' : distance}
   
      return result, status
   
   res = r.json()   
   
   return res, status

##############################
# Extract duration, distance #
##############################
def extract_duration_distance(res):
   
   duration = res['routes'][0]['duration']/60
   distance = res['routes'][0]['distance']
   
   return duration, distance

#################
# Extract route #
#################
def extract_route(res):
    
    route = polyline.decode(res['routes'][0]['geometry'])
    route = list(map(lambda data: [data[1],data[0]] ,route))
    
    return route

#####################
# Extract timestamp #
#####################
def extract_timestamp(route, duration):
    
    rt = np.array(route)
    rt = np.hstack([rt[:-1,:], rt[1:,:]])

    per = calculate_straight_distance(rt[:,1], rt[:,0], rt[:,3], rt[:,2])
    per = per / np.sum(per)

    timestamp = per * duration
    timestamp = np.hstack([np.array([0]),timestamp])
    timestamp = list(itertools.accumulate(timestamp)) 
    
    return timestamp
 
########
# MAIN #
########
# - input : O_point, D_point (shapely.geometry.Point type)
# - output : trip, timestamp, duration, distance
def osrm_routing_machine(OD_coords):
   # O_lat, O_lon, D_lat, D_lon = OD_coords
   osrm_base, status = get_res(OD_coords)
   
   if status == 'defined':
      duration, distance = extract_duration_distance(osrm_base)
      route = extract_route(osrm_base)
      timestamp = extract_timestamp(route, duration)
      
      result = {'route': route, 'timestamp': timestamp, 'duration': duration, 'distance' : distance}
      
      if np.isnan(result['timestamp'][-1]):
         result['timestamp'][-1] = 0.01
         result['duration'] = 0.01
         
      return result
   else: 
      return None

