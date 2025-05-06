import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go 

'''Vehicle Operation Status'''
def figure_4(base_path, time_range, time_single_labels, save_path = None):
    # Preprocess data
    total_records = []
    for fd_nm in os.listdir(base_path):
        records = pd.read_csv(base_path + fd_nm + '/record.csv')
        records = records[['time', 'waiting_passenger_cnt', 'empty_vehicle_cnt', 'driving_vehicle_cnt']]
        total_records.append(records)

    total_records = pd.concat(total_records).reset_index(drop=True)
    total_records = total_records.groupby('time').mean().reset_index()

    # Draw figure
    fig_4 = go.Figure()
    fig_4.add_trace(go.Scatter(x=total_records['time'].tolist(), y=total_records['waiting_passenger_cnt'].tolist(),
                            mode="lines", 
                            name="Waiting passengers",
                            line=dict(width=3),))
    fig_4.add_trace(go.Scatter(x=total_records['time'].tolist(), y=total_records['empty_vehicle_cnt'].tolist(),
                            mode="lines",
                            name="Idle vehicles",
                            line=dict(width=3),))
    fig_4.add_trace(go.Scatter(x=total_records['time'].tolist(), y=total_records['driving_vehicle_cnt'].tolist(),
                            mode="lines",
                            name="In-service vehicles",
                            line=dict(width=3),))
    fig_4.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = list(range(time_range[0], time_range[-1]+1, 60)),
            ticktext = time_single_labels + ['24:00'],
            range = [330, 1470],
            tickangle=45
        )
    )

    fig_4.update_xaxes(
        title_text = "Time")
    fig_4.update_yaxes(
            title_text = "Number of vehicles and passengers")

    fig_4.update_layout(
        legend={"x": 0.85, "y":0.95},
        margin={"l":0,"r":0,"b":0,"t":0,"pad":0},
        template="plotly_white")

    if save_path != None:
        fig_4.write_html(f"{save_path}figure_4.html", config={'responsive': True})
    else: 
        return fig_4
    
def figure_5(base_path, time_bins, time_single_labels, save_path = None):
    # Preprocess data 
    total_operating_vh_cnt = []
    for fd_nm in os.listdir(base_path):
        records = pd.read_csv(base_path + fd_nm + '/record.csv')
        records['operating_vehicle_cnt'] = records['empty_vehicle_cnt'] + records['driving_vehicle_cnt']
        records['time_cat'] = pd.cut(records['time'], bins=time_bins, labels=time_single_labels, right=False) 
        records = records[['time_cat', 'operating_vehicle_cnt']]
        
        operating_vh_cnt = records.groupby('time_cat').max('operating_vehicle_cnt').reset_index()
        total_operating_vh_cnt.append(operating_vh_cnt)

    total_operating_vh_cnt = pd.concat(total_operating_vh_cnt).reset_index(drop=True)
    total_operating_vh_cnt = total_operating_vh_cnt.groupby('time_cat').mean().reset_index()
    total_operating_vh_cnt['operating_vehicle_cnt'] = round(total_operating_vh_cnt['operating_vehicle_cnt']).astype(int)

    # Draw figure
    fig_5 = px.bar(x=total_operating_vh_cnt['time_cat'], y=total_operating_vh_cnt['operating_vehicle_cnt'])

    fig_5.update_layout(
        xaxis = dict(
            tickmode = 'array',
            title="Time",
            tickangle=45
            ),
        yaxis = dict(
            title="number of vehicles"),
        margin={"l":0,"r":20,"b":0,"t":0,"pad":0},
        template="plotly_white")

    fig_5.update_traces(
        textposition='outside',
        texttemplate=[f'<b>{cnt}</b>' for cnt in total_operating_vh_cnt['operating_vehicle_cnt']],
        textfont=dict(size=16, family='Arial Black')
    )

    if save_path != None:
        fig_5.write_html(f"{save_path}figure_5.html", config={'responsive': True})
    else:
        return fig_5    