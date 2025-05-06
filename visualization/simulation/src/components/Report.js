import {useEffect, useState } from 'react';
import '../css/report.css'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, registerables } from "chart.js";
import { Pie, Bar } from 'react-chartjs-2';
import legendImg from '../image/legend.png';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, ...registerables);


const currResult = (data, time) => {
    const result = data.find(v => Number(v.time) === Math.floor(time));
    return result || {};
}

export default function Report(props){

    const CURRENT_RESULT = currResult(props.data.RESULT, props.time);
    const CURRENT_WAITING_TIME = CURRENT_RESULT.current_waiting_time_dict;
    // console.log(CURRENT_WAITING_TIME);
    // const totalWaitingTime = HISTO_DATA.reduce((acc, time) => acc + time, 0);
    // const percentageData = HISTO_DATA.map(time => (time / totalWaitingTime) * 100);


    const data1 = {
        labels: ['Dispatched vehicles', 'Occupied vehicles', 'Idle vehicles'],
        datasets: [
          {
            label: 'count',
            data: [CURRENT_RESULT.dispatched_vehicle_num, 
                CURRENT_RESULT.occupied_vehicle_num, 
                CURRENT_RESULT.empty_vehicle_num],
            
            backgroundColor: [
                'rgba(23, 184, 190, 0.8)',
                'rgba(255, 153, 51, 0.8)',
                'rgba(255, 255, 255, 1.0)',
            ],
            borderColor: [
                'rgba(23, 184, 190, 0.8)',
                'rgba(255, 153, 51, 0.8)',
                'rgba(255, 255, 255, 1.0)',
            ],
            borderWidth: 0,
          },
        ],
      };
    const data2 = {
        labels: [5, 15, 25, 35, 45, 55],
        datasets: [
          {
            label: 'passenger (%)',
            data: Object.values(CURRENT_WAITING_TIME),
            borderColor: 'blue',
            Color: 'blue',
            fill: true,
            borderWidth: 0,
            barPercentage: 1,
            categoryPercentage: 1,
            hoverBackgroundColor: "darkgray",
            barThickness: "flex",
            backgroundColor: [
                'rgba(0, 0, 255, 0.5)'
            ]
          },
        ],
    };

    const options1= {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                display: true,
                labels: {
                    color: 'rgb(255, 255, 255)'
                }
            },
        }
    }    
    const options2= {
        maintainAspectRatio: false,
        responsive: true,
        plugins: {
            legend: {
                display: true,
                labels: {
                    color: 'rgb(255, 255, 255)'
                }
            },
        },
        scales: {
            x: {
                type: 'linear',
                ticks: {
                    color: 'white',
                    stepSize: 10,
                    max: 60,
                    callback: function (value) {
                        return value.toString();
                    }
                },
                title: {
                    display: true,
                    align: 'center',
                    text: 'Waiting time(min)',
                    color: 'rgb(255, 255, 255)'
                }
            },
            y: {
                suggestedMin: 0,
                suggestedMax: 100,
                ticks: {
                    stepSize: 20,
                    color: 'white'
                }
            }
        }
    }
    return(
        <div className="report-container">
            <h1 className='report-header'>REPORT</h1>
            <div className='chart-container'>
                <div>
                    <Pie className="chart1" data={data1} options={options1}></Pie>
                </div>
                <div>
                    <Bar className="chart2" data={data2} options={options2}></Bar>
                </div>
            </div>
            <div className='legend-container'>
                <img className='legend' src={legendImg}/>
            </div>
        </div>
    )
}