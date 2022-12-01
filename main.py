from simulation import Simulation
from objets import CarFactory, TrafficLight

sim = Simulation()

road_list = [{"id": 1, "type": "road", "start": (-60, 400), "end": (650, 200), "car_factory": CarFactory(["rand_color"], [0.2, 1.5])},
             {"id": 2, "type": "road", "start": (790, 200), "end": (1500, 400)},
             {"id": 3, "type": "arcroad", "start": 1, "end": 2}]


road_graph = {1: 3, 2: None, 3: 2}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.start_loop()
