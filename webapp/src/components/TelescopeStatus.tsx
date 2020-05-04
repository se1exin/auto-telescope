import React, {useEffect, useState} from 'react';
import io from 'socket.io-client';
import './TelescopeStatus.scss'
import {Status, StatusIndicator} from "./StatusIndicator";


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
    moving_to_position: boolean
    mpu_calibrated: boolean
    pitch: number
    roll: number
    success: boolean
    stepper_position: number
    target_position_x: number
    target_position_y: number
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
    moving_to_position: false,
    mpu_calibrated: false,
    pitch: 0,
    roll: 0,
    success: false,
    stepper_position: 0,
    target_position_x: 0,
    target_position_y: 0,
    yaw: 0,
    yaw_normalised: 0,
    yaw_smoothed: 0
}

export function TelescopeStatus() {

    let [socketConnected, setSocketConnected] = useState(false);

    let [status, setStatus] = useState<ITelescopeStatus>(initialStatus);

    useEffect(() => {
        console.log('MOUNT');
        socket.on('connect', () => {
            console.log('CONNECT');
            setSocketConnected(true);
        });

        socket.on('disconnect', () => {
            console.log('DISCONNECT');
            setStatus(initialStatus);
            setSocketConnected(false);
        });

        socket.on('status', (status: ITelescopeStatus) => setStatus(status))
    }, []);

    return (
        <div className={'telescope-status'}>
            <div className={'row'}>
                <StatusIndicator status={socketConnected ? Status.Success : Status.Error}/>
                { socketConnected ? 'Connected' : 'Disconnected' }
            </div>
            <div className={'row'}>
                <StatusIndicator status={status.mpu_calibrated ? Status.Success : Status.Error}/>
                MPU { status.mpu_calibrated ? 'Calibrated' : 'Not Calibrated' }
            </div>
            <div className={'row'}>
                { status.gps_updating ?
                    <>
                        <StatusIndicator status={status.gps_has_position ? Status.Success : Status.Warning}/>
                        GPS {status.gps_has_position ? 'Acquired' : 'Acquiring'}
                    </>
                    :
                    <>
                        <StatusIndicator status={Status.Error}/>
                        GPS Off
                    </>
                }
            </div>

            <div className={'row'}>
                { status.imu_updating ?
                    <>
                        <StatusIndicator status={status.imu_position_stable ? Status.Success : Status.Warning}/>
                        IMU {status.imu_position_stable ? 'Stable' : 'Unstable' }
                    </>
                    :
                    <>
                        <StatusIndicator status={Status.Error}/>
                        IMU Off
                    </>
                }

            </div>
            <div className={'row'}>
                <StatusIndicator status={status.moving_to_position ? Status.Warning : Status.Info}/>
                {status.moving_to_position ? 'Moving' : 'Not Moving' }
            </div>

            <div>
                Lat: { status.latitude }
            </div>
            <div>
                Lng: { status.longitude }
            </div>

            <div className={'circle'}>
                <div className={'pointer target-position'}
                     style={{'transform': `rotate(${status.target_position_x}deg` }}/>
                <div className={'pointer current-position-smoothed'}
                     style={{'transform': `rotate(${status.yaw_smoothed}deg` }}/>
                <div className={'pointer current-position'}
                     style={{'transform': `rotate(${status.yaw_normalised}deg` }}/>
                <div className={'pointer stepper-position'}
                     style={{'transform': `rotate(${status.stepper_position}deg` }}/>
            </div>
            <div>Yaw Target { status.target_position_x.toFixed(2) }</div>
            <div>Yaw Smoothed: { status.yaw_smoothed.toFixed(2) }</div>
            <div>Yaw Raw: { status.yaw_normalised.toFixed(2) }</div>
            <div>Stepper Pos: { status.stepper_position.toFixed(2) }</div>
        </div>
    )
}
