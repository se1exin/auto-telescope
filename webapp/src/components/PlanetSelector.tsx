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
    onSelect: (name: string) => void
    selectedPlanet: string
}

const planetMap = [
    {
        name: 'moon',
        img: imgMoon,
    },
    {
        name: 'mercury',
        img: imgMercury,
    },
    {
        name: 'venus',
        img: imgVenus,
    },
    {
        name: 'mars',
        img: imgMars,
    },
    {
        name: 'jupiter',
        img: imgJupiter,
    },
    {
        name: 'saturn',
        img: imgSaturn,
    },
    {
        name: 'uranus',
        img: imgUranus,
    },
    {
        name: 'neptune',
        img: imgNeptune,
    },
    {
        name: 'pluto',
        img: imgPluto,
    },
];

export function PlanetSelector(props: IPlanetSelectorProps) {

  const onClickPlanet = (name: string) => {
    props.onSelect(name);
  }

  return (
    <div className={'planet-selector'}>
        { planetMap.map((planet, index, ) => {
            let className = 'planet';
            if (props.selectedPlanet === planet.name) {
                className += ' selected';
            }
            return (
                <div
                    key={index}
                    className={className}
                    onClick={() => onClickPlanet(planet.name)}>
                    <img className={'image'}
                         src={planet.img}
                         alt={planet.name}
                    />
                    <div className={'details'}>
                        <span>{planet.name}</span>
                    </div>
                </div>
            )
        })}
    </div>
  )
}
