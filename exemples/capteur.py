"""Exemple de simulation utilisant un capteur. Pendant 60 secondes, le capteur enregistrera les vitesses, accélérations
et tailles des voitures qui lui passent devant, puis affiche ces données à la fin de la simulation."""

from traffsimpy import Simulation, CarFactory, TrafficLight, Sensor

sim = Simulation("Feu de signalisation", 1440, 820)

road_list = [{"id": 1, "type": "road", "start": (-60, 410), "end": (720, 410), "car_factory": CarFactory([2, 5], "rand_length"), "sign": TrafficLight(0)},
             {"id": 2, "type": "road", "start": 1, "end": (1500, 410), "sensors": Sensor(60, ["v", "a", "length"])}]

sim.create_roads(road_list)
sim.set_road_graph({1: 2, 2: None})

sim.start(60)

sim.print_sensors_results()
sim.plot_sensors_results()
