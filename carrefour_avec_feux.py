from simulation import Simulation
from objets import CarFactory, TrafficLight


sim = Simulation("Carrefour avec feux")

road_list = [{"id": 1, "type": "road", "start": (-60, 440), "end": (650, 440),  # routes de gauche
              "car_factory": CarFactory(["rand_color"], [1, 4.5]), "traffic_light": TrafficLight(0)},
             {"id": 2, "type": "road", "start": (650, 400), "end": (-60, 400)},

             {"id": 3, "type": "road", "start": (1500, 400), "end": (790, 400),  # routes de droite
              "car_factory": CarFactory(["rand_color"], [1, 4.5]), "traffic_light": TrafficLight(0)},
             {"id": 4, "type": "road", "start": (790, 440), "end": (1500, 440)},

             {"id": 5, "type": "road", "start": (700, -60), "end": (700, 350),  # routes du haut
              "car_factory": CarFactory(["rand_color"], [1, 4.5]), "traffic_light": TrafficLight(2)},
             {"id": 6, "type": "road", "start": (740, 350), "end": (740, -60)},

             {"id": 7, "type": "road", "start": (740, 900), "end": (740, 490),  # routes du bas
              "car_factory": CarFactory(["rand_color"], [1, 4.5]), "traffic_light": TrafficLight(2)},
             {"id": 8, "type": "road", "start": (700, 490), "end": (700, 900)},

             {"id": 14, "type": "road", "start": (650, 440), "end": (790, 440), "with_arrows": False},  # routes du carrefour
             {"id": 16, "type": "arcroad", "start": 1, "end": 6},
             {"id": 18, "type": "arcroad", "start": 1, "end": 8},

             {"id": 32, "type": "road", "start": (790, 400), "end": (650, 400), "with_arrows": False},
             {"id": 36, "type": "arcroad", "start": 3, "end": 6},
             {"id": 38, "type": "arcroad", "start": 3, "end": 8},

             {"id": 52, "type": "arcroad", "start": 5, "end": 2},
             {"id": 54, "type": "arcroad", "start": 5, "end": 4},
             {"id": 58, "type": "road", "start": (700, 350), "end": (700, 490), "with_arrows": False},

             {"id": 72, "type": "arcroad", "start": 7, "end": 2},
             {"id": 74, "type": "arcroad", "start": 7, "end": 4},
             {"id": 76, "type": "road", "start": (740, 490), "end": (740, 350), "with_arrows": False}]

road_graph = {1: {14: 0.3, 16: 0.4, 18: 0.3}, 14: 4, 16: 6, 18: 8, 2: None,
              3: {32: 0.3, 36: 0.4, 38: 0.3}, 32: 2, 36: 6, 38: 8, 4: None,
              5: {52: 0.3, 54: 0.4, 58: 0.3}, 52: 2, 54: 4, 58: 8, 6: None,
              7: {72: 0.3, 74: 0.4, 76: 0.3}, 72: 2, 74: 4, 76: 6, 8: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.start_loop()
