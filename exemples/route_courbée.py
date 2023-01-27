from traffsimpy import Simulation, CarFactory

sim = Simulation("Route courbée", 1440, 820)

road_list = [{"id": 1, "type": "road", "start": (-60, 300), "end": (600, 550), "car_factory": CarFactory("rand_color", 3)},
             {"id": 2, "type": "road", "start": (840, 550), "end": (1500, 300)},
             {"id": 3, "type": "arcroad", "start": 1, "end": 2}]

road_graph = {1: 3, 3: 2, 2: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)
sim.start()
