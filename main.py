from simulation import Simulation
from objets import CarFactory, CarSorter

sim = Simulation(1440, 840, logging_level=3)

cf = CarFactory(["rand_color", "{'a': 20, 'l': 100}"], lambda t: round(t, 2) % 3 == 0)
cs = CarSorter({2: 0.3, 3: 0.7})

road_list = [{"obj_id": 1, "start": (0, 700), "end": (1200, 550), "car_factory": cf},
             {"obj_id": 2, "start": (1188, 550), "end": (1188, 0)},
             {"obj_id": 3, "start": (1188, 550), "end": (1188, 840)},
             {"obj_id": 4, "start": (1250, 0), "end": (1250, 840), "car_factory": cf}]

road_graph = {1: cs, 2: None, 3: None, 4: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.start_loop()
