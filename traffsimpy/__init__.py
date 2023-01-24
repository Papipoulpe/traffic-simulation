import os

from .simulation import Simulation
from .components import CarFactory, TrafficLight, Sensor

os.chdir(os.path.dirname(__file__))

greetings = """
Bienvenue sur Traffic Simulation !

ESPACE : mettre en pause, FLÈCHE DROITE/HAUT : accélérer, FLÈCHE GAUCHE/BAS : ralentir, ENTRER : recentrer
"""

print(greetings)
