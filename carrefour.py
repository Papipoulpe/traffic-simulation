from simulation import Simulation
from objets import CarFactory, TrafficLight


sim = Simulation()

road_list = [{"id": 1, "type": "road", "start": (-60, 440), "end": (670, 440),  # routes de gauche
              "car_factory": CarFactory(["rand_color", "rand_length"], [0.2, 1.5]), "traffic_light": TrafficLight(False)},
             {"id": 2, "type": "road", "start": (670, 400), "end": (-60, 400)},

             {"id": 3, "type": "road", "start": (1500, 400), "end": (770, 400),  # routes de droite
              "car_factory": CarFactory(["rand_color", "rand_length"], [0.2, 1.5]), "traffic_light": TrafficLight(False)},
             {"id": 4, "type": "road", "start": (770, 440), "end": (1500, 440)},

             {"id": 5, "type": "road", "start": (700, -60), "end": (700, 370),  # routes du haut
              "car_factory": CarFactory(["rand_color", "rand_length"], [0.2, 1.5]), "traffic_light": TrafficLight(True)},
             {"id": 6, "type": "road", "start": (740, 370), "end": (740, -60)},

             {"id": 7, "type": "road", "start": (740, 900), "end": (740, 470),  # routes du bas
              "car_factory": CarFactory(["rand_color", "rand_length"], [0.2, 1.5]), "traffic_light": TrafficLight(True)},
             {"id": 8, "type": "road", "start": (700, 470), "end": (700, 900)},

             {"id": 14, "type": "road", "start": (670, 440), "end": (770, 440)},  # routes du carrefour
             {"id": 16, "type": "road", "start": (670, 440), "end": (740, 370)},
             {"id": 18, "type": "road", "start": (670, 440), "end": (700, 470)},

             {"id": 32, "type": "road", "start": (770, 400), "end": (670, 400)},
             {"id": 36, "type": "road", "start": (770, 400), "end": (740, 370)},
             {"id": 38, "type": "road", "start": (770, 400), "end": (700, 470)},

             {"id": 52, "type": "road", "start": (700, 370), "end": (670, 400)},
             {"id": 54, "type": "road", "start": (700, 370), "end": (770, 440)},
             {"id": 58, "type": "road", "start": (700, 370), "end": (700, 470)},

             {"id": 72, "type": "road", "start": (740, 470), "end": (670, 400)},
             {"id": 74, "type": "road", "start": (740, 470), "end": (770, 440)},
             {"id": 76, "type": "road", "start": (740, 470), "end": (740, 370)}]

road_graph = {1: {14: 0.3, 16: 0.4, 18: 0.3}, 14: 4, 16: 6, 18: 8, 2: None,
              3: {32: 0.3, 36: 0.4, 38: 0.3}, 32: 2, 36: 6, 38: 8, 4: None,
              5: {52: 0.3, 54: 0.4, 58: 0.3}, 52: 2, 54: 4, 58: 8, 6: None,
              7: {72: 0.3, 74: 0.4, 76: 0.3}, 72: 2, 74: 4, 76: 6, 8: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.start_loop()
