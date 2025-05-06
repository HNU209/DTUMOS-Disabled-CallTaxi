### 비슷한 단어 선택
from difflib import get_close_matches
def select_similar_word(word_to_compare, candidates):

    n = 1 # 최대 문자 매칭 개수
    cutoff = 0.6 # 유사도 하한
    
    close_matches = get_close_matches(word_to_compare, candidates, n, cutoff)

    return close_matches

### haversine
# - 위도, 경도를 통해 거리를 측정 (반환 km)
import numpy as np
def calculate_straight_distance(lat1, lon1, lat2, lon2):
    km_constant = 3959* 1.609344
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    km = km_constant * c
    return km

### route로 km 단위의 거리를 반환
# import numpy as np
def route_distance_calculater(data):
    distance = []

    for tr in data: 
        route = np.hstack([np.array(tr)[:-1], np.array(tr)[1:]])
        dis = sum(calculate_straight_distance(route[:,0], route[:,1], route[:,2], route[:,3]))
        distance.append(dis)
    
    return distance 


### meter를 위도, 경도 유클리드 거리로 변환
import osmnx as ox
def euclid_distance_cal(meter):

    #점 쌍 사이의 유클리드 거리를 계산
    dis_1 = ox.distance.euclidean_dist_vec(36.367658 , 127.447499, 36.443928, 127.419678)
    #직선거리 계산
    dis_2 = ox.distance.great_circle_vec(36.367658 , 127.447499, 36.443928, 127.419678)

    return dis_1/dis_2 * meter