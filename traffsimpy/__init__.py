import os

from .simulation import Simulation
from .components import CarFactory, TrafficLight, Sensor, Car, StopSign

os.chdir(os.path.dirname(__file__))

greetings = """
Bienvenue sur TraffSimPy !

ESPACE : mettre en pause
FLÈCHE DROITE/HAUT : accélérer
FLÈCHE GAUCHE/BAS : ralentir
DRAG : bouger
ENTRER : recentrer
S : faire une capture de la fenêtre
"""

print(greetings)
