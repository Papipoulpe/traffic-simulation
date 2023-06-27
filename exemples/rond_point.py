"""Exemple de simulation d'un rond-point où quatres doubles voies se rejoignent."""

from traffsimpy import Simulation, CarFactory


w, h = 1440, 840  # taille de la fenêtre
s = 140  # taille du rond point
ec = 25  # écart entre les routes
marg = 60  # marge en dehors de la fenêtre
ex_coeff = 0.37  # excentricité du rond-point

x_ouest = w / 2 - s
x_est = w / 2 + s
y_nord = h / 2 + s
y_sud = h / 2 - s

sud_ouest = x_ouest + s * (1 - ex_coeff), y_sud + s * (1 - ex_coeff)
vd_sud_ouest = (1, -1)
sud_est = x_est - s * (1 - ex_coeff), y_sud + s * (1 - ex_coeff)
vd_sud_est = (1, 1)
nord_est = x_est - s * (1 - ex_coeff), y_nord - s * (1 - ex_coeff)
vd_nord_est = (-1, 1)
nord_ouest = x_ouest + s * (1 - ex_coeff), y_nord - s * (1 - ex_coeff)
vd_nord_ouest = (-1, -1)

car_factory_settings = {"freq": [3, 8]}

sim = Simulation("Rond-point", w, h)

road_list = [
    {"id": 1, "s": (-marg, h / 2 - ec), "e": (x_ouest, h / 2 - ec),  # routes de gauche
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 2, "s": (x_ouest, h / 2 + ec), "e": (-marg, h / 2 + ec)},

    {"id": 3, "s": (w + marg, h / 2 + ec), "e": (x_est, h / 2 + ec),  # routes de droite
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 4, "s": (x_est, h / 2 - ec), "e": (w + marg, h / 2 - ec)},

    {"id": 5, "s": (w / 2 + ec, -marg), "e": (w / 2 + ec, y_sud),  # routes du bas
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 6, "s": (w / 2 - ec, y_sud), "e": (w / 2 - ec, -marg)},

    {"id": 7, "s": (w / 2 - ec, h + marg), "e": (w / 2 - ec, y_nord),  # routes du haut
     "car_factory": CarFactory(**car_factory_settings)},
    {"id": 8, "s": (w / 2 + ec, y_nord), "e": (w / 2 + ec, h + marg)},

    {"id": 9, "t": "a", "s": 1, "e": sud_ouest, "vde": vd_sud_ouest, "p": 1},  # routes du rond-point
    {"id": 10, "t": "a", "s": sud_ouest, "vds": vd_sud_ouest, "e": 6},
    {"id": 11, "t": "a", "s": sud_ouest, "vds": vd_sud_ouest, "e": sud_est, "vde": vd_sud_est, "p": 1},

    {"id": 12, "t": "a", "s": 5, "e": sud_est, "vde": vd_sud_est, "p": 1},
    {"id": 13, "t": "a", "s": sud_est, "vds": vd_sud_est, "e": 4},
    {"id": 14, "t": "a", "s": sud_est, "vds": vd_sud_est, "e": nord_est, "vde": vd_nord_est, "p": 1},

    {"id": 15, "t": "a", "s": 3, "e": nord_est, "vde": vd_nord_est, "p": 1},
    {"id": 16, "t": "a", "s": nord_est, "vds": vd_nord_est, "e": 8},
    {"id": 17, "t": "a", "s": nord_est, "vds": vd_nord_est, "e": nord_ouest, "vde": vd_nord_ouest, "p": 1},

    {"id": 18, "t": "a", "s": 7, "e": nord_ouest, "vde": vd_nord_ouest, "p": 1},
    {"id": 19, "t": "a", "s": nord_ouest, "vds": vd_nord_ouest, "e": 2},
    {"id": 20, "t": "a", "s": nord_ouest, "vds": vd_nord_ouest, "e": sud_ouest, "vde": vd_sud_ouest, "p": 1}]

road_graph = {
    1: 9, 5: 12, 3: 15, 7: 18,
    10: 6, 13: 4, 16: 8, 19: 2,
    9: {10: 0.7, 11: 0.3}, 12: {13: 0.7, 14: 0.3}, 15: {16: 0.7, 17: 0.3}, 18: {19: 0.7, 20: 0.3},
    11: {13: 0.5, 14: 0.5}, 14: {16: 0.5, 17: 0.5}, 17: {19: 0.5, 20: 0.5}, 20: {10: 0.5, 11: 0.5},
    6: None, 4: None, 8: None, 2: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)
sim.set_heavy_traffic_area(radius=150)

sim.run()
