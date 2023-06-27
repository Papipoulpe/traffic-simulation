"""Exemple de simulation d'une route droite avec un panneau stop au milieu."""

from traffsimpy import Simulation, CarFactory, StopSign

sim = Simulation("Panneau stop", 1440, 820)

road_list = [{"id": 1, "type": "road", "start": (-60, 410), "end": (720, 410), "car_factory": CarFactory(freq=[2, 4]), "sign": StopSign()},
             {"id": 2, "type": "road", "start": 1, "end": (1500, 410)}]

sim.create_roads(road_list)
sim.set_road_graph({1: 2, 2: None})
sim.run()
