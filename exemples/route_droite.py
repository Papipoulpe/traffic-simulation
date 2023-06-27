"""Exemple d'une simple route droite, où des voitures arrivent toutes les deux à quatre secondes et où la vitesse est
limitée à 13.9 m/s = 50 km/h.
"""

from traffsimpy import Simulation, CarFactory

sim = Simulation("Route droite", 1440, 820)
car_factory = CarFactory([2, 4])

sim.create_roads([{"type": "road", "start": (-60, 410), "end": (1500, 410), "v_max": 13.9, "car_factory": car_factory}])

sim.run()
