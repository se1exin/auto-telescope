import React, {useEffect, useState} from 'react';
import './StatusIndicator.scss';

export enum Status {
    Success = 'success',
    Error = 'error',
    Warning = 'warning',
    Info = 'info'
}

interface IStatusIndicator {
    status: Status
}

const BASE_CLASS = 'status-indicator';

export function StatusIndicator(props: IStatusIndicator) {
    let [className, setClassName] = useState(BASE_CLASS);

    useEffect(() => {
        setClassName(`${BASE_CLASS} ${props.status}`);
    }, [props.status]);

    return (
        <span className={className} />
    )
}
