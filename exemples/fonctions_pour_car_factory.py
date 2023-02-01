from traffsimpy import Simulation, CarFactory, Car


def freq_func(t):
    """Fonction de fréquence de création personnalisée pour CarFactory. Renvoie True si t est un carré parfait."""
    return round(t**0.5, 8).is_integer()


def crea_func(t):
    """Fonction de création personnalisée pour CarFactory. Renvoie une voiture dont la composante en bleu est une fonction affine du temps."""
    r, g, b = 120, 120, (8 * t) % 255
    return Car(color=(r, g, b))


sim = Simulation("Fonctions personnalisées pour CarFactory", 1440, 820)
car_factory = CarFactory(freq=freq_func, crea=crea_func)

sim.create_roads([{"type": "road", "start": (-60, 410), "end": (1500, 410), "car_factory": car_factory}])
sim.start()
