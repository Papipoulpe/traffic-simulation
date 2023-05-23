"""Exemple de simulation de carrefour de deux doubles voies."""

from traffsimpy import Simulation, CarFactory


w, h = 1440, 840  # taille de la fenêtre
s = 70  # taille du carrefour
ec = 20  # écart entre les routes
marg = 60  # marge en dehors de la fenêtre

x_ouest = w / 2 - s
x_est = w / 2 + s
y_nord = h / 2 + s
y_sud = h / 2 - s

car_factory_settings = {"freq": [3, 7.5], "crea": "rand_color"}

sim = Simulation("Carrefour", w, h)

road_list = [
    {"id": 1, "type": "road", "start": (-marg, h / 2 - ec), "end": (x_ouest, h / 2 - ec),  # routes de gauche
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 2, "type": "road", "start": (x_ouest, h / 2 + ec), "end": (-marg, h / 2 + ec)},

    {"id": 3, "type": "road", "start": (w + marg, h / 2 + ec), "end": (x_est, h / 2 + ec),  # routes de droite
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 4, "type": "road", "start": (x_est, h / 2 - ec), "end": (w + marg, h / 2 - ec)},

    {"id": 5, "type": "road", "start": (w / 2 + ec, -marg), "end": (w / 2 + ec, y_sud),  # routes du bas
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 6, "type": "road", "start": (w / 2 - ec, y_sud), "end": (w / 2 - ec, -marg)},

    {"id": 7, "type": "road", "start": (w / 2 - ec, h + marg), "end": (w / 2 - ec, y_nord),  # routes du haut
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 8, "type": "road", "start": (w / 2 + ec, y_nord), "end": (w / 2 + ec, h + marg)},

    {"id": 14, "type": "road", "start": 1, "end": 4, "with_arrows": False},  # routes du carrefour depuis 1
    {"id": 16, "type": "arcroad", "start": 1, "end": 6},
    {"id": 18, "type": "arcroad", "start": 1, "end": 8},

    {"id": 32, "type": "road", "start": 3, "end": 2, "with_arrows": False},  # routes du carrefour depuis 3
    {"id": 36, "type": "arcroad", "start": 3, "end": 6},
    {"id": 38, "type": "arcroad", "start": 3, "end": 8},

    {"id": 52, "type": "arcroad", "start": 5, "end": 2},  # routes du carrefour depuis 5
    {"id": 54, "type": "arcroad", "start": 5, "end": 4},
    {"id": 58, "type": "road", "start": 5, "end": 8, "with_arrows": False},

    {"id": 72, "type": "arcroad", "start": 7, "end": 2},  # routes du carrefour depuis 7
    {"id": 74, "type": "arcroad", "start": 7, "end": 4},
    {"id": 76, "type": "road", "start": 7, "end": 6, "with_arrows": False}]

road_graph = {
    1: {14: 0.3, 16: 0.4, 18: 0.3}, 14: 4, 16: 6, 18: 8, 2: None,
    3: {32: 0.3, 36: 0.4, 38: 0.3}, 32: 2, 36: 6, 38: 8, 4: None,
    5: {52: 0.3, 54: 0.4, 58: 0.3}, 52: 2, 54: 4, 58: 8, 6: None,
    7: {72: 0.3, 74: 0.4, 76: 0.3}, 72: 2, 74: 4, 76: 6, 8: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.run()
