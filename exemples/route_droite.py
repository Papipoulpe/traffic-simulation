from traffsimpy import Simulation, CarFactory

sim = Simulation("Route droite", 1440, 820)

sim.create_roads([{"type": "road", "start": (-60, 410), "end": (1500, 410), "v_max": 13.9, "car_factory": CarFactory(freq_func=2)}])
sim.start()
