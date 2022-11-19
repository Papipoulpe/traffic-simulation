import simulation

sim = simulation.Simulation(1440, 840, logging_level=3)

cf = simulation.CarFactory(["rand_color", "rand_length", "{'a': 20}"], lambda t: round(t, 2) % 3 == 0)

road_list = [{"obj_id": 1, "start": (0, 400), "end": (1200, 550), "car_factory": cf},
             {"obj_id": 2, "start": (1188, 550), "end": (1188, 0)},
             {"obj_id": 3, "start": (1188, 550), "end": (1188, 840)}]

road_graph = {1: {2: 0.3, 3: 0.7}, 2: None, 3: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.start_loop()
