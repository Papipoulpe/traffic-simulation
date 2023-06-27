![Logo](https://github.com/hcosserat/traffsimpy/blob/8744fe16985664e603d798de129f21a55fcbae51/branding/flat_logo.png)

# TraffSimPy

Module Python permettant de modéliser le trafic routier de n'importe quel réseau.

## Installation

Le module s'installe depuis [PyPi](https://pypi.org/project/traffsimpy/) :

`% pip3 install traffsimpy`

## Démarrage rapide

Simulons une route droite, où la vitesse des véhicules est limitée à 50 km/h et où des voitures arrivent toutes les deux secondes.

#### On importe les objets de bases du module

```
from traffsimpy import Simulation, CarFactory
```

L'objet Simulation gère l'affichage et la modélisation, l'objet CarFactory gère la création de nouveaux véhicules.

#### On crée un objet Simulation

```
sim = Simulation("Route droite", 1440, 820)
```

Le titre de la simulation sera "Route droite" et la fenêtre qui l'affichera sera de taille 1440×820.

#### On crée un objet CarFactory

```
freq = 2
car_factory = CarFactory(freq)
```

Il créera un nouveau véhicule toutes les deux secondes.

#### On définit le réseau routier

```
road = {"start": (-60, 410), 
"end": (1500, 410), 
"v_max": 13.9, 
"car_factory": car_factory}

sim.create_roads([road])
```

Il est constitué d'une seule route, qui va des points (-60, 410) à (1500, 410), qui a pour limite de vitesse 13.9 m/s ≈ 50 km/h et qui a pour usine à voitures le CarFactory définit précédement.

#### On lance la simulation

```
sim.run()
```

Elle restera ouverte jusqu'à ce que l'utilisateur quitte. Pendant la simulation, on peut ralentir, accélerer et arrêter le temps, bouger dans le réseau routier et prendre des captures d'écran.

## Utilisation



 