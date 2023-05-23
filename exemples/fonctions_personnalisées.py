"""Exemple de simulation d'une route droite avec des fonctions personnalisées pour CarFactory et le graphe des routes."""

from traffsimpy import Simulation, CarFactory, Car
from random import choice


def freq_func(t):
    """Fonction de fréquence de création personnalisée pour CarFactory. Renvoie True si t est un multiple de 5 ou de 11."""
    t_arrondi = round(t, 3)
    return t_arrondi % 5 == 0 or t_arrondi % 11 == 0


def crea_func(**_):
    """Fonction de création personnalisée pour CarFactory. Renvoie une voiture, une camionnette ou un camion."""
    config_voiture = {"length": 4, "a_max": 1, "t_react": 1}
    config_camionette = {"length": 6, "a_max": 0.9, "t_react": 1.5}
    config_camion = {"length": 8, "a_max": 0.8, "t_react": 2}
    config = choice([config_voiture, config_camionette, config_camion])
    return Car(**config)


def sort_func(t):
    """Fonction de tri personnalisée pour le graphe des routes. Renvoie l'identifiant de route 12 ou 13 en changeant
    toutes les 10 secondes.
    """
    if t % 20 <= 10:
        return 12
    else:
        return 13


sim = Simulation("Fonctions personnalisées pour CarFactory", 1440, 820)
car_factory = CarFactory(freq=freq_func, crea=crea_func)

road_list = [{"id": 1, "type": "road", "start": (-60, 410), "end": (950, 410), "car_factory": car_factory},
             {"id": 2, "type": "road", "start": (1050, 330), "end": (1050, -20)},
             {"id": 3, "type": "road", "start": (1050, 490), "end": (1050, 840)},
             {"id": 12, "type": "arcroad", "start": 1, "end": 2},
             {"id": 13, "type": "arcroad", "start": 1, "end": 3}]

road_graph = {1: sort_func, 12: 2, 13: 3}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)
sim.run()
