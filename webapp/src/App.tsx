import React from 'react';
import './App.scss';

import {TelescopeStatus} from "./components/TelescopeStatus";

function App() {
  return (
    <div className="App">
        <div className={"status-hud"}>
            <TelescopeStatus />
        </div>
    </div>
  );
}

export default App;
