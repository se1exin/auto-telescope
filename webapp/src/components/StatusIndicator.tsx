import React from 'react';

export enum Status {
    Success = 'success',
    Error = 'error',
    Warning = 'warning',
    Info = 'info'
}

interface IStatusIndicator {
    status: Status,
    title?: string
}

export function StatusIndicator(props: IStatusIndicator) {
    return (
        <div className={'status-indicator'}>
            <span className={`indicator ${props.status}`} />
            <span className={'title'}>{props.title}</span>
        </div>
    )
}
