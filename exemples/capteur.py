"""Exemple de simulation utilisant des capteurs. Pendant 60 secondes, les capteurs enregistreront les vitesses,
accélérations, tailles et historiques des distances parcourues et vitesses des voitures qui lui passent devant, puis
affichent et génèrent un graphique de ces données à la fin de la simulation.
"""

from traffsimpy import Simulation, CarFactory, TrafficLight, Sensor

sim = Simulation("Feu de signalisation", 1440, 820)

sensors = [Sensor(0.5, ["v", "a"]), Sensor(0.6, "length"), Sensor(0.7, "d(t)"), Sensor(0.8, "v(t)")]

road_list = [{"id": 1, "type": "road", "start": (-60, 410), "end": (720, 410), "car_factory": CarFactory([2, 5], "rand_length"), "sign": TrafficLight(0)},
             {"id": 2, "type": "road", "start": 1, "end": (1500, 410), "sensors": sensors}]

sim.create_roads(road_list)
sim.set_road_graph({1: 2, 2: None})

sim.run(60)

sim.compute_sensors_results()
sim.print_sensors_results()
sim.plot_sensors_results()
