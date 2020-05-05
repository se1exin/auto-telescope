import React from 'react';

export interface IFlyWheelProps {
  current_pos: number
  estimated_pos: number
  raw_pos: number
  smoothed_pos: number
  target_pos: number
}

export function FlyWheel(props: IFlyWheelProps) {
  return (
    <div className={'fly-wheel'}>
      <div className={'circle'}>
        <div className={'pointer target-pos'}
             style={{'transform': `rotate(${props.target_pos}deg`}}/>
        <div className={'pointer estimated-pos'}
             style={{'transform': `rotate(${props.estimated_pos}deg`}}/>
        <div className={'pointer smoothed-pos'}
             style={{'transform': `rotate(${props.smoothed_pos}deg`}}/>
        <div className={'pointer current-pos'}
             style={{'transform': `rotate(${props.current_pos}deg`}}/>
        <div className={'pointer raw-pos'}
             style={{'transform': `rotate(${props.raw_pos}deg`}}/>
      </div>
      <div className={'text target-pos'}>
        Target: <span className={'value'}>{ props.target_pos.toFixed(2) }</span>
      </div>
      <div className={'text estimated-pos'}>
        Estimated: <span className={'value'}>{ props.estimated_pos.toFixed(2) }</span>
      </div>
      <div className={'text smoothed-pos'}>
        Smoothed: <span className={'value'}>{ props.smoothed_pos.toFixed(2) }</span>
      </div>
      <div className={'text current-pos'}>
        Current: <span className={'value'}>{ props.current_pos.toFixed(2) }</span>
      </div>
      <div className={'text raw-pos'}>
        Raw: <span className={'value'}>{ props.raw_pos.toFixed(2) }</span>
      </div>
    </div>
  )
}
