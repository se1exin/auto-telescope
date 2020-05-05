import React from 'react';
import imgJupiter from "../images/jupiter-planet.png";
import imgMars from "../images/mars-planet.png";
import imgMercury from "../images/mercury-planet.png";
import imgMoon from "../images/moon-satellite.png";
import imgNeptune from "../images/neptune-planet.png";
import imgPluto from "../images/pluto-dwarf-planet.png";
import imgSaturn from "../images/saturn-planet.png";
import imgUranus from "../images/uranus-planet.png";
import imgVenus from "../images/venus-planet.png";

export interface IPlanetSelectorProps {
}

export function PlanetSelector(props: IPlanetSelectorProps) {

  const onClickPlanet = (name: string) => {
    console.log('onclick', name);
  }

  return (
    <div className={'planet-selector'}>
      <div
        className={'planet'}
        onClick={() => onClickPlanet('moon')}>
        <img className={'image'} src={imgMoon} />
        <div className={'details'}>
          <span>Moon</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('mercury')}>
        <img className={'image'} src={imgMercury} />
        <div className={'details'}>
          <span>Mercury</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('venus')}>
        <img className={'image'} src={imgVenus} />
        <div className={'details'}>
          <span>Venus</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('mars')}>
        <img className={'image'} src={imgMars} />
        <div className={'details'}>
          <span>Mars</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('jupiter')}>
        <img className={'image'} src={imgJupiter} />
        <div className={'details'}>
          <span>Jupiter</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('saturn')}>
        <img className={'image'} src={imgSaturn} />
        <div className={'details'}>
          <span>Saturn</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('uranus')}>
        <img className={'image'} src={imgUranus} />
        <div className={'details'}>
          <span>Uranus</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('neptune')}>
        <img className={'image'} src={imgNeptune} />
        <div className={'details'}>
          <span>Neptune</span>
        </div>
      </div>

      <div
        className={'planet'}
        onClick={() => onClickPlanet('pluto')}>
        <img className={'image'} src={imgPluto} />
        <div className={'details'}>
          <span>Pluto</span>
        </div>
      </div>
    </div>
  )
}
