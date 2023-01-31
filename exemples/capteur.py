from traffsimpy import Simulation, CarFactory, TrafficLight, Sensor

sim = Simulation("Feu de signalisation", 1440, 820)

road_list = [{"id": 1, "type": "road", "start": (-60, 410), "end": (720, 410), "car_factory": CarFactory(["rand_length", "rand_color"], [2, 5]), "traffic_light": TrafficLight(0)},
             {"id": 2, "type": "road", "start": 1, "end": (1500, 410), "sensors": Sensor(60, ["v", "a", "length"])}]

sim.create_roads(road_list)
sim.set_road_graph({1: 2, 2: None})

sim.start(60)

sim.print_sensors_results()
sim.plot_sensors_results()
