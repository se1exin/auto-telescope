import React, {useEffect, useState} from 'react';
import './App.scss';
import axios from "axios";

import io from "socket.io-client";
import {StatusBar} from "./components/StatusBar";
import {FlyWheel} from "./components/FlyWheel";
import {PlanetSelector} from "./components/PlanetSelector";

interface IGPSStatus {
  latitude: number
  longitude: number
  declination: number
  is_updating: boolean
  has_position: boolean
}

interface IIMUStatus {
  is_updating: boolean
  has_position: boolean
  position_stable: boolean
  imu_calibrated: boolean
  mag_calibrated: boolean
  mpu_calibrated: boolean
  roll_raw: number
  pitch_raw: number
  yaw_raw: number
  roll_filtered: number
  pitch_filtered: number
  yaw_filtered: number
  roll_smoothed: number
  pitch_smoothed: number
  yaw_smoothed: number
}

export interface ITelescopeStatus {
  gps: IGPSStatus
  imu: IIMUStatus
  moving_to_target: boolean
  success: boolean
  started: boolean
  stepper_position: number
  target_position_x: number
  target_position_y: number
  target_found: boolean
}

const API_ADDRESS = "http://10.1.1.19:8080";
const socket = io(API_ADDRESS);
const initialStatus: ITelescopeStatus = {
  gps: {
    latitude: 0,
    longitude: 0,
    declination: 0,
    is_updating: false,
    has_position: false,
  },
  imu: {
    is_updating: false,
    has_position: false,
    position_stable: false,
    imu_calibrated: false,
    mag_calibrated: false,
    mpu_calibrated: false,
    roll_raw: 0.0,
    pitch_raw: 0.0,
    yaw_raw: 0.0,
    roll_filtered: 0.0,
    pitch_filtered: 0.0,
    yaw_filtered: 0.0,
    roll_smoothed: 0.0,
    pitch_smoothed: 0.0,
    yaw_smoothed: 0.0,
  },
  moving_to_target: false,
  success: false,
  started: false,
  stepper_position: 0,
  target_position_x: 0,
  target_position_y: 0,
  target_found: false,
}

function App() {
  let [socketConnected, setSocketConnected] = useState(false);

  let [status, setStatus] = useState<ITelescopeStatus>(initialStatus);

  const [selectedPlanet, setSelectedPlanet] = useState('');

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
      if (result.data.exception) {
        alert(result.data.exception);
      }
    }).catch(() => {
      setPositionDisabled(false);
    })
  }

  const onPressCancelPosition = () => {
    axios.post(`${API_ADDRESS}/position/cancel`);
  }

  const onSelectPlanet = (name: string) => {
    axios.post(`${API_ADDRESS}/planet`, {'name': name}).then(result => {
      setPositionDisabled(false);
      if (result.data.success) {
        setSelectedPlanet(name);
      } else if (result.data.exception) {
        alert(result.data.exception);
      }
    }).catch(() => {
      setPositionDisabled(false);
    })
  }

  return (
    <div className="app">
      <StatusBar
        connected={socketConnected}
        gps_has_position={status.gps.has_position}
        gps_updating={status.gps.is_updating}
        imu_has_position={status.imu.has_position}
        imu_position_stable={status.imu.position_stable}
        imu_updating={status.imu.is_updating}
        moving_to_target={status.moving_to_target}
        started={status.started}
        target_found={status.target_found}
      />

      <div className={'main'}>
        <FlyWheel
            current_pos={status.imu.yaw_filtered}
            estimated_pos={status.stepper_position}
            raw_pos={status.imu.yaw_raw}
            smoothed_pos={status.imu.yaw_smoothed}
            target_pos={status.target_position_x}
        />
        <PlanetSelector
            onSelect={onSelectPlanet}
            selectedPlanet={selectedPlanet}
        />
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
