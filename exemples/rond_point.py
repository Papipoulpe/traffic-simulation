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

car_factory_settings = {"freq": [3, 7.5], "crea": "rand_color"}

sim = Simulation("Rond-point", w, h)

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

    {"id": 9, "type": "arcroad", "start": 1, "end": sud_ouest, "vdend": vd_sud_ouest},  # routes du rond-point
    {"id": 10, "type": "arcroad", "start": sud_ouest, "vdstart": vd_sud_ouest, "end": 6},
    {"id": 11, "type": "arcroad", "start": sud_ouest, "vdstart": vd_sud_ouest, "end": sud_est, "vdend": vd_sud_est},

    {"id": 12, "type": "arcroad", "start": 5, "end": sud_est, "vdend": vd_sud_est},
    {"id": 13, "type": "arcroad", "start": sud_est, "vdstart": vd_sud_est, "end": 4},
    {"id": 14, "type": "arcroad", "start": sud_est, "vdstart": vd_sud_est, "end": nord_est, "vdend": vd_nord_est},

    {"id": 15, "type": "arcroad", "start": 3, "end": nord_est, "vdend": vd_nord_est},
    {"id": 16, "type": "arcroad", "start": nord_est, "vdstart": vd_nord_est, "end": 8},
    {"id": 17, "type": "arcroad", "start": nord_est, "vdstart": vd_nord_est, "end": nord_ouest, "vdend": vd_nord_ouest},

    {"id": 18, "type": "arcroad", "start": 7, "end": nord_ouest, "vdend": vd_nord_ouest},
    {"id": 19, "type": "arcroad", "start": nord_ouest, "vdstart": vd_nord_ouest, "end": 2},
    {"id": 20, "type": "arcroad", "start": nord_ouest, "vdstart": vd_nord_ouest, "end": sud_ouest, "vdend": vd_sud_ouest}]

road_graph = {
    1: 9, 5: 12, 3: 15, 7: 18,
    10: 6, 13: 4, 16: 8, 19: 2,
    9: {10: 0.7, 11: 0.3}, 12: {13: 0.7, 14: 0.3}, 15: {16: 0.7, 17: 0.3}, 18: {19: 0.7, 20: 0.3},
    11: {13: 0.5, 14: 0.5}, 14: {16: 0.5, 17: 0.5}, 17: {19: 0.5, 20: 0.5}, 20: {10: 0.5, 11: 0.5},
    6: None, 4: None, 8: None, 2: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)
sim.set_bumping_zone(radius=150)

sim.start()
