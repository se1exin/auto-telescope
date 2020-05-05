import React from 'react';
import {Status, StatusIndicator} from "./StatusIndicator";

export interface IStatusBarProps {
  connected: boolean
  gps_has_position: boolean
  gps_updating: boolean
  imu_has_position: boolean
  imu_position_stable: boolean
  imu_updating: boolean
  moving_to_position: boolean
  started: boolean
}

export function StatusBar(props: IStatusBarProps) {
  return (
    <div className={'status-bar'}>
      <div className={'col'}>
        <StatusIndicator
          status={props.connected ? Status.Success : Status.Error}
          title={props.connected ? 'Connected' : 'Disconnected'}
        />
      </div>
      <div className={'col'}>
        <StatusIndicator
          status={props.started ? Status.Success : Status.Error}
          title={ props.started ? 'Initialised' : 'Not Initialised' }
        />

      </div>
      <div className={'col'}>
        { props.gps_has_position ?
          <>
            <StatusIndicator
              status={Status.Success}
              title={'GPS Acquired'}
            />
          </>
          :
          <>
            <StatusIndicator
              status={props.gps_updating ? Status.Warning : Status.Error}
              title={`GPS ${props.gps_updating ? 'Acquiring' : 'Off'}`}
            />

          </>
        }
      </div>

      <div className={'col'}>
        { props.imu_updating ?
          <>
            <StatusIndicator
              status={props.imu_position_stable ? Status.Success : Status.Warning}
              title={`IMU ${props.imu_position_stable ? 'Stable' : 'Unstable' }`}
            />
          </>
          :
          <>
            <StatusIndicator
              status={Status.Error}
              title={'IMU Off'}
            />

          </>
        }
      </div>
      <div className={'col'}>
        <StatusIndicator
          status={props.moving_to_position ? Status.Warning : Status.Success}
          title={props.moving_to_position ? 'Targeting...' : 'Target Found' }
        />
      </div>
    </div>
  )
}
