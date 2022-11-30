from simulation import Simulation
from objets import CarFactory, TrafficLight

sim = Simulation()

road_list = [{"obj_id": 1, "start": (-60, 440), "end": (670, 440),  # routes de gauche
              "car_factory": CarFactory(["rand_color"], [0.2, 1.5]), "traffic_light": TrafficLight(False)},
             {"obj_id": 2, "start": (670, 400), "end": (-60, 400)},

             {"obj_id": 3, "start": (1500, 400), "end": (770, 400),  # routes de droite
              "car_factory": CarFactory(["rand_color"], [0.2, 1.5]), "traffic_light": TrafficLight(False)},
             {"obj_id": 4, "start": (770, 440), "end": (1500, 440)},

             {"obj_id": 5, "start": (700, -60), "end": (700, 370),  # routes du haut
              "car_factory": CarFactory(["rand_color"], [0.2, 1.5]), "traffic_light": TrafficLight(True)},
             {"obj_id": 6, "start": (740, 370), "end": (740, -60)},

             {"obj_id": 7, "start": (740, 900), "end": (740, 470),  # routes du bas
              "car_factory": CarFactory(["rand_color"], [0.2, 1.5]), "traffic_light": TrafficLight(True)},
             {"obj_id": 8, "start": (700, 470), "end": (700, 900)},

             {"obj_id": 14, "start": (670, 440), "end": (770, 440)},  # routes du carrefour
             {"obj_id": 16, "start": (670, 440), "end": (740, 370)},
             {"obj_id": 18, "start": (670, 440), "end": (700, 470)},

             {"obj_id": 32, "start": (770, 400), "end": (670, 400)},
             {"obj_id": 36, "start": (770, 400), "end": (740, 370)},
             {"obj_id": 38, "start": (770, 400), "end": (700, 470)},

             {"obj_id": 52, "start": (700, 370), "end": (670, 400)},
             {"obj_id": 54, "start": (700, 370), "end": (770, 440)},
             {"obj_id": 58, "start": (700, 370), "end": (700, 470)},

             {"obj_id": 72, "start": (740, 470), "end": (670, 400)},
             {"obj_id": 74, "start": (740, 470), "end": (770, 440)},
             {"obj_id": 76, "start": (740, 470), "end": (740, 370)}]

road_graph = {1: {14: 0.3, 16: 0.4, 18: 0.3}, 14: 4, 16: 6, 18: 8, 2: None,
              3: {32: 0.3, 36: 0.4, 38: 0.3}, 32: 2, 36: 6, 38: 8, 4: None,
              5: {52: 0.3, 54: 0.4, 58: 0.3}, 52: 2, 54: 4, 58: 8, 6: None,
              7: {72: 0.3, 74: 0.4, 76: 0.3}, 72: 2, 74: 4, 76: 6, 8: None}

sim.create_roads(road_list)
sim.set_road_graph(road_graph)

sim.start_loop()
