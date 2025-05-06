import React, { useState, useEffect } from 'react';
import { Map } from 'react-map-gl';
import {AmbientLight, PointLight, LightingEffect} from '@deck.gl/core';
import { TripsLayer } from '@deck.gl/geo-layers';
import { ScatterplotLayer, IconLayer } from '@deck.gl/layers';
import ICON_PNG from '../image/icon-atlas.png';
import DeckGL from '@deck.gl/react';
import '../css/trip.css';

const ambientLight = new AmbientLight({
  color: [255, 255, 255],
  intensity: 1.0
});
  
const pointLight = new PointLight({
  color: [255, 255, 255],
  intensity: 2.0,
  position: [-74.05, 40.7, 8000]
});

const lightingEffect = new LightingEffect({ambientLight, pointLight});

const material = {
  ambient: 0.1,
  diffuse: 0.6,
  shininess: 32,
  specularColor: [60, 64, 70]
};

const DEFAULT_THEME = {
  trailColor0: [253, 128, 93],
  trailColor1: [23, 184, 190],
  material,
  effects: [lightingEffect]
};

const INITIAL_VIEW_STATE = {
  longitude: 126.9917937,
  latitude: 37.5518911,
  zoom: 11,
  minZoom: 2,
  maxZoom: 20,
  pitch: 0,
  bearing: 0
};

const mapStyle = 'mapbox://styles/spear5306/ckzcz5m8w002814o2coz02sjc';
const MAPBOX_TOKEN = `pk.eyJ1Ijoic3BlYXI1MzA2IiwiYSI6ImNremN5Z2FrOTI0ZGgycm45Mzh3dDV6OWQifQ.kXGWHPRjnVAEHgVgLzXn2g`; 

const currData = (data, time) => {
  const arr = [];
  data.forEach(v => {
    const [start, end] = v.timestamp;
    if ((start <= time) & (time <= end)) {
      arr.push(v.location);
    };
  });
  return arr;
}

const currResult = (data, time) => {
  const result = data.find(v => Number(v.time) === Math.floor(time));
  return result;
}


const ICON_MAPPING = {
  marker: {x: 0, y: 0, width: 128, height: 128, mask: true}
};

const Trip = (props) => {
  const animationSpeed = 5;
  const time = props.time;
  const minTime = props.minTime;
  const maxTime = props.maxTime;

  const DRIVER = props.data.DRIVER_TRIP;
  const D_MARKER = currData(props.data.DRIVER_MARKER, time);
  const P_MARKER = currData(props.data.PASSENGER_MARKER, time);

  const CURRENT_RESULT = currResult(props.data.RESULT, time);

  const [animationFrame, setAnimationFrame] = useState('');

  const animate = () => {
    props.setTime(time => {
      if (time > maxTime) {
        return minTime;
      } else {
        return time + (0.01) * animationSpeed;
      };
    });
    const af = window.requestAnimationFrame(animate);
    setAnimationFrame(af);
  };

  useEffect(() => {
    animate();
    return () => window.cancelAnimationFrame(animationFrame);
  }, []);

  const layers = [
    new TripsLayer({
      id: 'DRIVER',
      data: DRIVER,
      getPath: d => d.trip,
      getTimestamps: d => d.timestamp,
      getColor: d => d.board === 1 ? [255, 153, 51] : [23, 184, 190],
      opacity: 0.7,
      widthMinPixels: 5,
      trailLength: 1,
      currentTime: time,
      shadowEnabled: false,
    }),
    new ScatterplotLayer({
      id: 'driver-marker',
      data: D_MARKER,
      getPosition: d => d,
      getFillColor: [255, 255, 255],
      getRadius: 3,
      opacity: 0.5,
      pickable: false,
      radiusScale: 4,
      radiusMinPixels: 4,
      radiusMaxPixels: 8,
    }),
    new IconLayer({
      id: 'passenger-marker',
      data: P_MARKER,
      pickable: false,
      iconAtlas: ICON_PNG,
      iconMapping: ICON_MAPPING,
      sizeMinPixels: 20,
      sizeMaxPixels: 15,
      sizeScale: 5,
      getIcon: d => 'marker',
      getPosition: d => d,
      getSize: d => 10,
      getColor: d => [255, 255, 0]
    }),
  ];

  return (
    <div className='trip-container' style={{position: 'relative'}}>
      <DeckGL
        effects={DEFAULT_THEME.effects}
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        layers={layers}
      >
        <Map
          mapStyle={mapStyle}
          mapboxAccessToken={MAPBOX_TOKEN}
        />
      </DeckGL>
      <h1 className='time'>
        TIME : {(String(parseInt(Math.round(time) / 60) % 24).length === 2) ? parseInt(Math.round(time) / 60) % 24 : '0'+String(parseInt(Math.round(time) / 60) % 24)} : {(String(Math.round(time) % 60).length === 2) ? Math.round(time) % 60 : '0'+String(Math.round(time) % 60)}
      </h1>
      <div className='subtext'>
        <div>- Total number of Vehicles in-service&nbsp; {CURRENT_RESULT.driving_vehicle_num+CURRENT_RESULT.empty_vehicle_num}</div>
        <div>- Number of Vehicles in Service&nbsp;: {CURRENT_RESULT.driving_vehicle_num}</div>
        <div>- Number of Idle Vehicles&nbsp;: {CURRENT_RESULT.empty_vehicle_num}</div>
        <div>- Number of Waiting Passengers&nbsp;: {CURRENT_RESULT.waiting_passenger_num}</div>
        <div>- Current Average Waiting Time (minute)&nbsp;: {CURRENT_RESULT.average_waiting_time}</div>
        <div>- Cumulative Number of Request Failure&nbsp;: {CURRENT_RESULT.fail_passenger_cumNum}</div>
      </div>
    </div>
  );
}

export default Trip;