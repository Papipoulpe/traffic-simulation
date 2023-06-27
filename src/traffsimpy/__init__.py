from .simulation import Simulation
from .components import CarFactory, TrafficLight, Sensor, Car, StopSign
from .settings import simulation_configuration


__version__ = "1.0.12"

greetings = """
Bienvenue sur TraffSimPy !

ESPACE : mettre en pause
FLÈCHE DROITE/HAUT : accélérer
FLÈCHE GAUCHE/BAS : ralentir
DRAG : bouger
ENTRER : recentrer
S : faire une capture de la fenêtre
ESC : terminer la simulation
"""

print(greetings)
