"""Exemple de simulation d'une route droite avec des fonctions personnalisées : une voiture dont la composante en bleu
de sa couleur dépend du temps sera créée à chaque fois que le nombre de seconde depuis le début de la simualtion est un
carré parfait."""

from traffsimpy import Simulation, CarFactory, Car
from random import choice


def freq_func(t):
    """Fonction de fréquence de création personnalisée pour CarFactory. Renvoie True si t est un multiple de 5 ou de 11."""
    t_arrondi = round(t, 3)
    return t_arrondi % 5 == 0 or t_arrondi % 11 == 0


def crea_func(t):
    """Fonction de création personnalisée pour CarFactory. Renvoie une voiture, une camionnette ou un camion."""
    config_voiture = {"length": 4, "a_max": 1, "t_react": 1}
    config_camionette = {"length": 6, "a_max": 0.9, "t_react": 1.5}
    config_camion = {"length": 8, "a_max": 0.8, "t_react": 2}
    config = choice([config_voiture, config_camionette, config_camion])
    return Car(**config)


sim = Simulation("Fonctions personnalisées pour CarFactory", 1440, 820)
car_factory = CarFactory(freq=freq_func, crea=crea_func)

sim.create_roads([{"type": "road", "start": (-60, 410), "end": (1500, 410), "car_factory": car_factory}])
sim.start()
