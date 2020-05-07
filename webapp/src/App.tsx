import React, {useEffect, useState} from 'react';
import './App.scss';
import axios from "axios";

import io from "socket.io-client";
import {StatusBar} from "./components/StatusBar";
import {FlyWheel} from "./components/FlyWheel";
import {PlanetSelector} from "./components/PlanetSelector";

export interface ITelescopeStatus {
  declination: number
  gps_has_position: boolean
  gps_updating: boolean
  imu_calibrated: boolean
  imu_has_position: boolean
  imu_position_stable: boolean
  imu_updating: boolean
  latitude: number
  longitude: number
  mag_calibrated: boolean
  mag_heading_raw: number
  moving_to_target: boolean
  mpu_calibrated: boolean
  pitch: number
  roll: number
  success: boolean
  started: boolean
  stepper_position: number
  target_position_x: number
  target_position_y: number
  target_found: boolean
  yaw: number
  yaw_normalised: number
  yaw_smoothed: number
}

const API_ADDRESS = "http://10.1.1.19:8080";
const socket = io(API_ADDRESS);
const initialStatus: ITelescopeStatus = {
  declination: 0,
  gps_has_position: false,
  gps_updating: false,
  imu_calibrated: false,
  imu_has_position: false,
  imu_position_stable: false,
  imu_updating: false,
  latitude: 0,
  longitude: 0,
  mag_calibrated: false,
  mag_heading_raw: 0,
  moving_to_target: false,
  mpu_calibrated: false,
  pitch: 0,
  roll: 0,
  success: false,
  started: false,
  stepper_position: 0,
  target_position_x: 0,
  target_position_y: 0,
  target_found: false,
  yaw: 0,
  yaw_normalised: 0,
  yaw_smoothed: 0
}

function App() {
  let [socketConnected, setSocketConnected] = useState(false);

  let [status, setStatus] = useState<ITelescopeStatus>(initialStatus);

  useEffect(() => {
    socket.on('connect', () => setSocketConnected(true));

    socket.on('disconnect', () => {
      setStatus(initialStatus);
      setSocketConnected(false);
    });

    socket.on('status', (status: ITelescopeStatus) => setStatus(status))
  }, []);


  let [startDisabled, setStartDisabled] = useState(false);
  const onPressStart = () => {
    setStartDisabled(true);
    axios.post(`${API_ADDRESS}/start`).then(result => {
      console.log(result);
      setStartDisabled(false);
    }).catch(() => {
      setStartDisabled(false);
    })
  }

  let [positionDisabled, setPositionDisabled] = useState(false);
  let [targetPosition, setTargetPosition] = useState('0');
  const onPressPosition = () => {
    let position = parseFloat(targetPosition);
    if (isNaN(position)) {
      setTargetPosition('0');
      return;
    }
    setPositionDisabled(true);
    axios.post(`${API_ADDRESS}/position`, {'x': position}).then(result => {
      console.log(result);
      setPositionDisabled(false);
    }).catch(() => {
      setPositionDisabled(false);
    })
  }

  const onPressCancelPosition = () => {
    axios.post(`${API_ADDRESS}/position/cancel`);
  }

  const onSelectPlanet = (name: string) => {
    console.log('planet', name);
    axios.post(`${API_ADDRESS}/planet`, {'name': name}).then(result => {
      console.log(result);
      setPositionDisabled(false);
    }).catch(() => {
      setPositionDisabled(false);
    })
  }

  return (
    <div className="app">
      <StatusBar
        connected={socketConnected}
        gps_has_position={status.gps_has_position}
        gps_updating={status.gps_updating}
        imu_has_position={status.imu_has_position}
        imu_position_stable={status.imu_position_stable}
        imu_updating={status.imu_updating}
        moving_to_target={status.moving_to_target}
        started={status.started}
        target_found={status.target_found}
      />

      <div className={'main'}>
        <FlyWheel
            current_pos={status.yaw_normalised}
            estimated_pos={status.stepper_position}
            raw_pos={status.mag_heading_raw}
            smoothed_pos={status.yaw_smoothed}
            target_pos={status.target_position_x}
        />
        <PlanetSelector onSelect={onSelectPlanet} />
      </div>

      <div className={'control-bar'}>
        { !status.started &&
          <button
              className={'start-button'}
              onClick={onPressStart}
              disabled={startDisabled}
          >Initialise Telescope</button>
        }
        { (status.started && !status.moving_to_target) &&
        <>
          <button
              onClick={onPressPosition}
              disabled={positionDisabled}
          >Target Position</button>
          <input
              value={targetPosition}
              onChange={event => setTargetPosition(event.target.value)}
              onFocus={event => event.target.select()}
              disabled={positionDisabled}
          />
        </>
        }
        {(status.started && status.moving_to_target) &&
        <button onClick={onPressCancelPosition}>Cancel Targeting</button>
        }
      </div>
    </div>
  );
}

export default App;
