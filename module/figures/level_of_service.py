import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go 
from plotly.subplots import make_subplots

'''Level Of Service'''
def figure_1(base_path, time_range, time_bins, time_single_labels, save_path = None):
    ### Preprocess data
    file_num = len(os.listdir(base_path))
    total_request_cnt_inf = []

    for fd_nm in os.listdir(base_path):
        passengers = pd.read_json(base_path + fd_nm + '/passenger_marker.json')
        passengers['start_time'] = [tm[0] for tm in passengers['timestamp']]
        passengers['end_time'] = [tm[-1] for tm in passengers['timestamp']]
        passengers['time_cat'] = pd.cut(passengers['start_time'], bins=time_bins, labels=time_single_labels, right=False)

        failure_passengers = passengers.loc[(passengers['status'] == 0)].reset_index(drop=True)
        failure_passengers['time_cat'] = pd.cut(failure_passengers['end_time'], bins=time_bins, labels=time_single_labels, right=False) # 실패 건수는 실패 시간을 기준
        
        request_ps_cnt = pd.DataFrame(passengers['time_cat'].value_counts().sort_index()).reset_index()
        failure_ps_cnt = pd.DataFrame(failure_passengers['time_cat'].value_counts().sort_index()).reset_index()    

        request_ps_cnt = request_ps_cnt.rename(columns={"count": "request_count"})
        failure_ps_cnt = failure_ps_cnt.rename(columns={"count": "failure_count"})

        request_cnt_inf = pd.merge(request_ps_cnt, failure_ps_cnt, on='time_cat')
        request_cnt_inf = request_cnt_inf.rename(columns={'time_cat': 'time'})
        total_request_cnt_inf.append(request_cnt_inf)

    average_request_cnt_inf = pd.concat(total_request_cnt_inf).groupby('time').sum().reset_index()
    average_request_cnt_inf['request_count'] = average_request_cnt_inf ['request_count'] / file_num
    average_request_cnt_inf['failure_count'] = average_request_cnt_inf ['failure_count'] / file_num
    average_request_cnt_inf['time'] = [tm for tm in range(time_range[0], time_range[1], 60)]

    ### Draw figure
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=average_request_cnt_inf["time"], y=average_request_cnt_inf["request_count"],
                            mode="lines+markers", 
                            name="called passenger",
                            line=dict(width=3),
                            opacity=0.8))
    fig1.add_trace(go.Scatter(x=average_request_cnt_inf["time"],
                              y=average_request_cnt_inf["failure_count"],
                              mode="lines+markers",
                              name="Passengers who failed to call",
                              line=dict(width=3),
                              opacity=0.8))
    fig1.update_layout(
        xaxis = dict(
            tickmode = 'array',
            tickvals = average_request_cnt_inf["time"].tolist(),
            ticktext = time_single_labels
        )
    )
    fig1.update_xaxes(
        range=[time_range[0]-25, time_range[1]-50],
        title_text = "Time")
    fig1.update_yaxes(
            title_text = "Number of passengers")

    fig1.update_layout(
        legend={"x": 0.8, "y":1},
        margin={"l":0,"r":0,"b":0,"t":0,"pad":0},
        template="plotly_white")

    if save_path != None:
        fig1.write_html(f"{save_path}figure_1.html", config={'responsive': True})
    else: 
        return fig1
    
# import os
# import pandas as pd
# import plotly.graph_objects as go 
def figure_2(base_path, time_bins, time_single_labels, time_double_labels, save_path = None):
    ### Preprocess data
    file_num = len(os.listdir(base_path))
    total_service_level_inf = []

    for fd_nm in os.listdir(base_path):
        passengers = pd.read_json(base_path + fd_nm + '/passenger_marker.json')
        passengers['start_time'] = [tm[0] for tm in passengers['timestamp']]
        passengers['end_time'] = [tm[-1] for tm in passengers['timestamp']]
        passengers['waiting_time'] = passengers['end_time'] - passengers['start_time']
        passengers['time_cat'] = pd.cut(passengers['start_time'], bins=time_bins, labels=time_single_labels, right=False) 
        request_count = pd.DataFrame(passengers.value_counts('time_cat').sort_index()).reset_index()
        request_count = request_count.rename(columns={'count': 'request_count'})

        ## service failure ratio
        success_passengers = passengers.loc[(passengers['status'] == 1)].reset_index(drop=True)
        success_passengers['time_cat'] = pd.cut(success_passengers['start_time'], bins=time_bins, labels=time_single_labels, right=False) 
        service_failure = success_passengers.loc[(success_passengers['waiting_time'] >= 30)].reset_index(drop=True)
        
        service_failure_ratio = pd.DataFrame(service_failure.value_counts('time_cat').sort_index() / success_passengers.value_counts('time_cat').sort_index()).reset_index()
        service_failure_ratio = service_failure_ratio.rename(columns={'count': "service_failure_ratio"})
        
        ## request failure ratio
        failure_passengers = passengers.loc[(passengers['status'] == 0)].reset_index(drop=True)
        failure_passengers['time_cat'] = pd.cut(failure_passengers['end_time'], bins=time_bins, labels=time_single_labels, right=False) # 실패 건수는 실패 시간을 기준
        
        request_failure_ratio = pd.DataFrame(failure_passengers.value_counts('time_cat').sort_index() / passengers.value_counts('time_cat').sort_index()).reset_index()
        request_failure_ratio = request_failure_ratio.rename(columns={'count': "request_failure_ratio"})
        
        
        service_level_inf = (request_count
                        .merge(service_failure_ratio, on='time_cat')
                        .merge(request_failure_ratio, on='time_cat'))
        total_service_level_inf.append(service_level_inf)

    average_service_level_inf = pd.concat(total_service_level_inf).groupby('time_cat').mean().reset_index()
    average_service_level_inf['service_failure_ratio'] = round(average_service_level_inf['service_failure_ratio'], 2) * 100
    average_service_level_inf['request_failure_ratio'] = round(average_service_level_inf['request_failure_ratio'], 2) * 100

    ### Draw figure
    fig_2 = go.Figure()
    # ── 1) traces ──
    # (a) 실제 bar trace
    fig_2.add_trace(go.Bar(
        x=time_double_labels,
        y=average_service_level_inf['request_count'].tolist(),
        name='Called Requests',
        marker=dict(color='grey'),
        opacity=0.5,
        showlegend=False     # legend는 직접 그릴 거라 꺼둠
    ))
    # (b) 두 개의 line trace
    for col, nm in [
        ('request_failure_ratio', 'Request Failure (%)'),
        ('service_failure_ratio', 'Service Failure (%)')
    ]:
        fig_2.add_trace(go.Scatter(
            x=time_double_labels,
            y=average_service_level_inf[col].tolist(),
            mode='lines+markers',
            name=nm,
            yaxis='y2',
            line=dict(width=3),
            opacity=0.8
        ))

    # ── 2) “Called Requests” 회색 박스 + 텍스트 ──
    # (a) 작은 회색 박스 그리기
    fig_2.add_shape(
        type='rect',
        xref='paper', yref='paper',
        x0=0.02, x1=0.05,    # 박스의 너비 조절
        y0=0.93, y1=0.96,    # 박스의 높이 조절
        fillcolor='grey',
        line_width=0
    )
    # (b) 그 옆에 텍스트
    fig_2.add_annotation(
        xref='paper', yref='paper',
        x=0.055, y=0.945,
        xanchor='left', yanchor='middle',
        text='Called Requests',
        showarrow=False,
        font=dict(size=12, color='black')
    )

    # ── 3) 레이아웃 ──
    fig_2.update_layout(
        template='plotly_white',
        xaxis=dict(
            type='category',
            title='Time',
            tickangle=45,
            categoryorder='array',
            categoryarray=time_double_labels
        ),
        yaxis=dict(
            title='Number of Passengers',
            nticks=6,              
            range=[0, 1000],
            gridcolor='lightgrey',
            showgrid=False,
        ),
        yaxis2=dict(
            title='Percentage (%)',
            overlaying='y',
            side='right',
            range=[-5, 100],
            nticks=6,
            gridcolor='lightgrey'
        ),
        legend=dict(x=0.8, y=1),  
        margin=dict(l=0, r=0, t=0, b=0, pad=0),
    )

    if save_path != None:
        fig_2.write_html(f"{save_path}figure_2.html", config={'responsive': True})
    else: 
        return fig_2
    
    
# import numpy as np
# import pandas as pd
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
def figure_3(base_path, time_range, time_bins, time_single_labels, save_path = None):
    ### Preprocess data
    total_waiting_time_inf = []
    for fd_nm in os.listdir(base_path):
        passengers = pd.read_json(base_path + fd_nm + '/passenger_marker.json')
        passengers['start_time'] = [tm[0] for tm in passengers['timestamp']]
        passengers['end_time'] = [tm[-1] for tm in passengers['timestamp']]
        passengers['waiting_time'] = passengers['end_time'] - passengers['start_time']
        passengers['time_cat'] = pd.cut(passengers['start_time'], bins=time_bins, labels=time_single_labels, right=False) 
        waiting_time_inf = passengers[['time_cat', 'waiting_time']]
        total_waiting_time_inf.append(waiting_time_inf)
        
    total_waiting_time_inf = pd.concat(total_waiting_time_inf).reset_index(drop=True)
    total_waiting_time_inf['time'] = [int(tm.split(':')[0])*60 for tm in total_waiting_time_inf['time_cat']]

    # top5 평균 대기시간
    top5pct_average_wt = {}
    for tm in time_single_labels:
        specific_waiting_time = total_waiting_time_inf.loc[(total_waiting_time_inf['time_cat'] == tm)].reset_index(drop=True)
        threshold = specific_waiting_time['waiting_time'].quantile(0.95)
        top5pct_waiting_time = specific_waiting_time[specific_waiting_time['waiting_time'] >= threshold]
        
        top5pct_average_waiting_time = np.mean(top5pct_waiting_time['waiting_time'])
        top5pct_average_wt[tm] = round(top5pct_average_waiting_time, 2)


    ### Draw figure
    # 평균 대기시간 계산
    mean_wait = round(np.mean(total_waiting_time_inf["waiting_time"]))

    # 4:1 비율의 1행 2열 서브플롯 생성
    fig_3 = make_subplots(
        rows=1, cols=2,
        column_widths=[0.8, 0.2],
        subplot_titles=(
            "Passenger waiting time by hour",
            f"Total waiting time <br>(average: {mean_wait} minute)"
        )
    )

    # ── 왼쪽: 시간대별 Box + Top 5% 선 ──
    fig_3.add_trace(
        go.Box(
            x=total_waiting_time_inf["time"],
            y=total_waiting_time_inf["waiting_time"],
            showlegend=False,
            # marker_color="grey",
            boxpoints="outliers"
        ),
        row=1, col=1
    )
    fig_3.add_trace(
        go.Scatter(
            x=list(range(time_range[0], time_range[1], 60)),
            y=list(top5pct_average_wt.values()),
            mode="lines+markers",
            name="Top 5%",
            line=dict(width=3),
            opacity=0.8
        ),
        row=1, col=1
    )

    # ── 오른쪽: 전체 기간 분포 Box ──
    fig_3.add_trace(
        go.Box(
            y=total_waiting_time_inf["waiting_time"],
            showlegend=False,
            # marker_color="lightgrey",
            boxpoints="outliers"
        ),
        row=1, col=2
    )

    # ── 레이아웃 및 축 설정 ──
    fig_3.update_xaxes(
        dict(
            tickmode="array",
            tickvals=[i for i in range(time_range[0], time_range[1], 60)],
            ticktext=time_single_labels,
            tickangle=45,
        ),
        row=1, col=1
    )
    fig_3.update_xaxes(visible=False, row=1, col=2)

    fig_3.update_yaxes(title_text="Waiting Time (minute)", row=1, col=1)
    fig_3.update_yaxes(title_text="", row=1, col=2)

    fig_3.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=True,
        legend=dict(x=0.6, y=1.1)
    )
    if save_path != None:
        fig_3.write_html(f"{save_path}figure_3.html", config={'responsive': True})
    else: 
        return fig_3