import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point    
import plotly.graph_objects as go 
import plotly.express as px

def figure_6_7_N_8_9(base_path, place_geometry, mapboxKey, time_range, status='pickup', save_path = None):
    ### Preprocess data
    total_trips = []
    for fd_nm in os.listdir(base_path):
        trips = pd.read_json(base_path + fd_nm + '/trip.json')
        
        if status == 'pickup':
            pickup_trips = trips.loc[(trips['board'] == 0)].reset_index(drop=True)
            
            pickup_trips['lon'] = [tp[0][0] for tp in pickup_trips['trip']]
            pickup_trips['lat'] = [tp[0][1] for tp in pickup_trips['trip']]

            pickup_trips['time'] = [ts[0] for ts in pickup_trips['timestamp']]
            total_trips.append(pickup_trips)
        else:
            dropoff_trips = trips.loc[(trips['board'] == 1)].reset_index(drop=True)

            dropoff_trips['lon'] = [tp[-1][0] for tp in dropoff_trips['trip']]
            dropoff_trips['lat'] = [tp[-1][1] for tp in dropoff_trips['trip']]

            dropoff_trips['time'] = [ts[-1] for ts in dropoff_trips['timestamp']]
            total_trips.append(dropoff_trips)
        
    total_trips = pd.concat(total_trips).reset_index(drop=True)
    total_trips["time"] = pd.cut(total_trips["time"],
                                        right=False,
                                        bins = list(range(time_range[0], time_range[1]+1, 60)),
                                        labels = list(range(time_range[0], time_range[1], 60)))
    total_trip_frames = [row for _,row in total_trips.groupby('time')] # 데이터 frame화

    ### Draw figure_6
    frames = [{
        'name':f'frame_{idx}',
        'data':[{
            'type':'densitymapbox',
            'lat':i["lat"].tolist(),
            'lon':i["lon"].tolist(),
            'showscale': False,
            'radius':4}],           
    } for idx,i in enumerate(total_trip_frames)]  

    sliders = [{
        'transition':{'duration': 0},
        'x':0.11, 
        'y':0.04,
        'len':0.80,
        'steps':[
            {
                'label':f"{idx+int(time_range[0]/60)}".zfill(2),
                'method':'animate',
                'args':[
                    ['frame_{}'.format(idx)],
                    {'mode':'immediate', 'frame':{'duration':100, 'redraw': True}, 'transition':{'duration':100}}
                ],
            } for idx,_ in enumerate(total_trip_frames)]
    }]

    play_button = [{
        'type':'buttons',
        'showactive':True,
        'x':0.1, 'y':-0.05,
        'buttons':[{ 
            'label': 'Play',
            'method':'animate',
            'args':[
                None,
                {
                    'frame':{'duration':500, 'redraw':True},
                    'transition':{'duration':100},
                    'fromcurrent':True,
                    'mode':'immediate',
                }
            ]
        }]
    }]

    # Defining the initial state
    data = frames[0]['data']

    # Adding all sliders and play button to the layout
    layout = go.Layout(
        sliders=sliders,
        updatemenus=play_button,
        mapbox={
            'accesstoken': mapboxKey,
            'center':{"lat": place_geometry['lat'].iloc[0], "lon":place_geometry['lon'].iloc[0]},
            'zoom':10,
            'style':'light'},
        margin = {'l':0, 'r':0, 'b':80, 't':0},
    )

    # Creating the figure
    fig_anima = go.Figure(data=data, layout=layout, frames=frames)

    ### Draw figure_7
    data = go.Densitymapbox(lat=total_trips.lat,
                            lon=total_trips.lon,
                            radius=1.2)

    layout_basic = go.Layout(
        mapbox={
            'accesstoken': mapboxKey,
            'center':{"lat": place_geometry['lat'].iloc[0], "lon":place_geometry['lon'].iloc[0]},
            'zoom':10,
            'style':'light'},
        margin = {'l':0, 'r':0, 'b':0, 't':0},
        template="plotly_white"
    )

    fig_htm = go.Figure(data=data, layout=layout_basic)

    if save_path != None:
        if status == 'pickup':
            fig_anima.write_html(f"{save_path}figure_6.html", config={'responsive': True})
            fig_htm.write_html(f"{save_path}figure_7.html", config={'responsive': True})
        else:
            fig_anima.write_html(f"{save_path}figure_8.html", config={'responsive': True})
            fig_htm.write_html(f"{save_path}figure_9.html", config={'responsive': True})
    else:
        return fig_anima, fig_htm
    
def figure_10(base_path, place_geometry, region_boundary, mapboxKey, save_path = None):
    ### Preprocess data
    total_failure_ps = []
    for fd_nm in os.listdir(base_path):
        passengers = pd.read_json(base_path + fd_nm + '/passenger_marker.json')
        failure_passengers = passengers.loc[(passengers['status'] == 0)].reset_index(drop=True)
        
        failure_passengers['geometry'] = [Point(geo) for geo in failure_passengers['location']]
        failure_passengers = gpd.GeoDataFrame(failure_passengers[['geometry']], geometry='geometry', crs=4326)
        failure_passengers = gpd.sjoin(failure_passengers, region_boundary)
        total_failure_ps.append(failure_passengers)
        
    total_failure_ps = pd.concat(total_failure_ps).reset_index(drop=True)

    average_failure_ps = total_failure_ps.groupby(['temp']).count().reset_index()
    average_failure_ps = average_failure_ps[['temp','geometry']].rename(columns={'geometry':'Number Of Failure'})
    average_failure_ps['Number Of Failure'] = round((average_failure_ps['Number Of Failure'] / 10))
    average_failure_ps = pd.merge(region_boundary, average_failure_ps, how='left', on='temp')
    average_failure_ps['Number Of Failure'] = average_failure_ps['Number Of Failure'].fillna(0)
    average_failure_ps.index = average_failure_ps.temp

    ### Draw figure
    fig_10 = px.choropleth_mapbox(average_failure_ps,
                            geojson=average_failure_ps.geometry,
                            locations=average_failure_ps.index,
                            color="Number Of Failure",
                            center={"lat": place_geometry['lat'].iloc[0], "lon": place_geometry['lon'].iloc[0]},
                            mapbox_style="carto-positron",
                            zoom=10)
    fig_10.update_layout(
        mapbox={
            'accesstoken':mapboxKey,
            'style':'light'},
        margin={"r":0,"t":0,"l":0,"b":0},
        )

    if save_path != None:
        fig_10.write_html(f"{save_path}figure_10.html", config={'responsive': True})
    else:
        return fig_10

def figure_11(base_path, place_geometry, region_boundary, mapboxKey, save_path = None):
    ### Preprocess data 
    total_waiting_time_by_region = []
    for fd_nm in os.listdir(base_path):
        passengers = pd.read_json(base_path + fd_nm + '/passenger_marker.json')
        passengers['waiting_time'] = [tm[-1]-tm[0] for tm in passengers['timestamp']]
        
        passengers['geometry'] = [Point(geo) for geo in passengers['location']]
        passengers = gpd.GeoDataFrame(passengers[['waiting_time', 'geometry']], geometry='geometry', crs=4326)
        passengers = gpd.sjoin(passengers, region_boundary)
        
        passengers = passengers.groupby(["temp"]).mean(["wait_time"]).reset_index().drop("index_right",axis=1)
        passengers = pd.merge(region_boundary, passengers, how='left', on='temp')
        passengers['waiting_time'] = passengers['waiting_time'].fillna(0)
        total_waiting_time_by_region.append(passengers)
        
    average_waiting_time_by_region = pd.concat(total_waiting_time_by_region).groupby('temp').mean('waiting_time').reset_index()
    average_waiting_time_by_region = average_waiting_time_by_region.rename(columns={'waiting_time':'Wait Time (min)'})
    average_waiting_time_by_region = pd.merge(region_boundary, average_waiting_time_by_region, on='temp')
    average_waiting_time_by_region.index = average_waiting_time_by_region.temp

    ### Draw figure
    fig_11 = px.choropleth_mapbox(average_waiting_time_by_region,
                            geojson=average_waiting_time_by_region.geometry,
                            locations=average_waiting_time_by_region.index,
                            color="Wait Time (min)",
                            center={"lat": place_geometry['lat'].iloc[0], "lon": place_geometry['lon'].iloc[0]},
                            mapbox_style="carto-positron",
                            zoom=10)
    fig_11.update_layout(
        mapbox={
            'accesstoken':mapboxKey,
            'style':'light'},
        margin={"r":0,"t":0,"l":0,"b":0},
        )

    if save_path != None:
        fig_11.write_html(f"{save_path}figure_11.html", config={'responsive': True})
    else:
        return fig_11