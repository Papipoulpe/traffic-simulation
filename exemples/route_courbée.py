"""Exemple d'une simple route courbée permettant la jonction entre deux routes droites non alignées."""

from traffsimpy import Simulation, CarFactory

sim = Simulation("Route courbée", 1440, 820)

road_list = [{"id": 1, "type": "road", "start": (-60, 100), "end": (300, 300), "car_factory": CarFactory([2, 4])},
             {"id": 2, "type": "road", "start": (1140, 300), "end": (1500, 100)},
             {"id": 3, "type": "arcroad", "start": 1, "end": 2}]

road_graph = {1: 3, 3: 2, 2: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)
sim.run()
