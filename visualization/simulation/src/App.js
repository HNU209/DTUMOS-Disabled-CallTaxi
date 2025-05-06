import 'mapbox-gl/dist/mapbox-gl.css';
import React, { useEffect, useState } from 'react';
import Slider from '@mui/material/Slider';
import axios, * as others from 'axios';
import Trip from './components/Trip';
import Report from './components/Report';
import Splash from './components/Splash';
import './css/app.css';


const getRestData = dataName => {
  const res = axios.get(`https://raw.githubusercontent.com/HNU209/DTUMOS-Disabled-CallTaxi_simulation/main/src/data/${dataName}.json`);
  // const res = axios.get(`./data/${dataName}.json`);
  const result = res.then(r => r.data);
  return result;
}

const App = () => {
  const minTime = 360;
  const maxTime = 1439;
  const initTripData = 1;

  const [time, setTime] = useState(minTime);
  const [data, setData] = useState({
    DRIVER_TRIP: [],
    DRIVER_MARKER: [],
    PASSENGER_MARKER: [],
    RESULT : [],
    check: [],
  });
  const [loaded, setLoaded] = useState(false);
  
  // init
  useEffect(() => {
    async function getFetchData() {
      const startTimeArray = [...Array(initTripData).keys()].map(t => t + minTime);

      const DRIVER_TRIP = await getRestData('trip');
      const DRIVER_MARKER = await getRestData('vehicle_marker');
      const PASSENGER_MARKER = await getRestData('passenger_marker');
      const RESULT = await getRestData('result');

      if (DRIVER_TRIP && DRIVER_MARKER && PASSENGER_MARKER && RESULT) {
        setData(prev => ({
          ...prev,
          DRIVER_TRIP: [...data.DRIVER_TRIP, ...DRIVER_TRIP],
          DRIVER_MARKER: [...data.DRIVER_MARKER, ...DRIVER_MARKER],
          PASSENGER_MARKER: [...data.PASSENGER_MARKER, ...PASSENGER_MARKER],
          RESULT: [...data.RESULT, ...RESULT],
          check: [...data.check, ...startTimeArray]
        }));
        setLoaded(true);
      };
    };

    getFetchData();
  }, []);

  useEffect(() => {
    const requestTime = Math.floor(time) + initTripData;
  }, [Math.floor(time)]);

  const SliderChange = value => {
    const time = value.target.value;
    setTime(time);
  };

  return (
    <div className='container'>
      {
        loaded ?
        <>
          <Trip
            data={data}
            minTime={minTime}
            maxTime={maxTime}
            time={time}
            setTime={setTime}
          >
          </Trip>
          <Slider id="slider" value={time} min={minTime} max={maxTime} onChange={SliderChange} track="inverted"/>
          <Report
            data={data}
            minTime={minTime}
            maxTime={maxTime}
            time={time}
            setTime={setTime}
          >
          </Report>
        </>
        :
        <Splash />
      }
    </div>
  );
};

export default App;
