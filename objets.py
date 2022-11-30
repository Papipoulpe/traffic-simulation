from mathsandutils import *
import settings as s


class CarFactory:
    def __init__(self, crea_func=None, fact_func=None, obj_id=None):
        """
        Création de voitures à l'entrée d'une route.

        :param crea_func: choix de voiture à créer, "{'arg': val}" puis "rand_color", "rand_length" et/ou "rand_width"
        :param fact_func: fréquence de création de voiture, fonction ou [a, b] pour fréquence aléatoire
        """
        self.id = new_id(self, obj_id)

        if isinstance(crea_func, (str, list)) or crea_func is None:
            self.crea_func = self.generic_creafunc(crea_func)
        else:
            self.crea_func = crea_func

        if isinstance(fact_func, list):
            self.fact_func = self.generic_factfunc(fact_func)
        else:
            self.fact_func = fact_func

    def __str__(self):
        return f"CarFactory(id={self.id})"

    def factory(self, args_crea, args_fact):
        """
        :param args_crea: args de choix
        :param args_fact: args de fréquence de création
        """
        if self.fact_func and self.fact_func(**args_fact):
            returning = self.crea_func(**args_crea)
            log(f"{self} is creating {returning}", 2)
            return returning

    @staticmethod
    def generic_creafunc(func_name):
        if isinstance(func_name, str):
            func_name = [func_name]

        attrs = {"v": s.CAR_V, "a": s.CAR_A, "color": s.CAR_COLOR, "width": s.CAR_WIDTH, "le": s.CAR_LENGTH, "obj_id": None}

        def crea_func(*args, **kwargs):
            if "rand_color" in func_name:
                attrs["color"] = [np.random.randint(s.CAR_RAND_COLOR_MIN, s.CAR_RAND_COLOR_MAX) for _ in range(3)]
            if "rand_length" in func_name:
                attrs["le"] = np.random.randint(s.CAR_RAND_WIDTH_MIN, s.CAR_RAND_WIDTH_MAX)
            if "rand_width" in func_name:
                attrs["width"] = np.random.randint(s.CAR_RAND_LENGTH_MIN, s.CAR_RAND_LENGTH_MAX)
            try:
                attrs_dic = parse(func_name[0])
                log("Cannot parse crea_func", 2)
            except ValueError:
                attrs_dic = {}
            for key in attrs_dic:
                attrs[key] = attrs_dic[key]
            return Car(**attrs)

        return crea_func

    @staticmethod
    def generic_factfunc(func_name):
        if func_name[0] == func_name[1]:  # si func_name est de type [a, a]
            def fact_func(t, last_car):
                return round(t, 2) % func_name[0] == 0 and (not last_car or last_car.d > last_car.length + s.DD_MIN)
            return fact_func
        else:
            def fact_func(t, last_car):  # TODO: pas terrible
                mod = np.random.uniform(func_name[0], func_name[1])
                return round(t % mod, 2) == 0 and (not last_car or last_car.d > last_car.length + s.DD_MIN)
            return fact_func


class CarSorter:
    def __init__(self, method=None):
        """
        Gestion des voitures à la sortie d'une route.

        :param method: Dictionnaire associant une probabilité à une autre route, fonction de tri, None
        """
        if isinstance(method, dict):  # si la méthode est un dict de proba
            self.method = "probs"
            probs, roads = [], []
            for p in method:
                probs.append(method[p])
                roads.append(p)

            def sort_func(*args, **kwargs):
                return ids[np.random.choice(roads, p=probs)]

        elif method is None:  # si la méthode est None, les voitures sont supprimées
            self.method = None
            sort_func = empty

        else:
            self.method = "func"
            sort_func = method

        self.sort_func = sort_func

    def sorter(self, *args, **kwargs):
        return self.sort_func(*args, **kwargs)


class Car:
    def __init__(self, v, a, le, width, color, obj_id):
        """
        Voiture.

        :param v: vitesse
        :param a: acceleration
        :param le: longueur
        :param width: largeur
        :param color: couleur
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.color = color
        self.length, self.width = le, width

        self.d = 0  # distance du derrière depuis le début de la route
        self.x, self.y = 0, 0  # position du mileu du derrière dans la fenêtre
        self.v = v  # vitesse
        self.a = a  # acceleration

        self.coins = ((0, 0), (0, 0), (0, 0), (0, 0))  # coordonnées des coins, pour affichage

    def __str__(self):
        return f"Car(id={self.id}, x={self.x}, y={self.y}, d={self.d}, v={self.v}, a={self.a}, coins={rec_round(self.coins)}, color{self.color})"

    def update_mvt(self, dt, prev_car):
        """
        Actualise les coordonnées du mouvement.

        :param dt: durée du mouvement
        :param prev_car: éventuelle voiture devant
        """

        idm(self, prev_car, dt)

    def update_coins(self, vd):
        """
        Actualise les coins selon la position.

        :param vd: vecteur directeur de la route
        """
        vdx, vdy = vd
        vnx, vny = vect_norm(vd, self.width / 2)
        c1 = self.x + vnx, self.y + vny
        c2 = self.x - vnx, self.y - vny
        c3 = self.x - vnx + self.length * vdx, self.y - vny + self.length * vdy
        c4 = self.x + vnx + self.length * vdx, self.y + vny + self.length * vdy
        self.coins = c1, c2, c3, c4


class TrafficLight:
    def __init__(self, green: bool, delay: float = s.TL_DELAY, obj_id: int = None):
        self.id = new_id(self, obj_id)
        self.road: Road = ...  # route auquel le feu est rattaché
        self.coins = (0, 0), (0, 0), (0, 0), (0, 0)  # coins pour affichage
        self.width = s.TL_WIDTH

        self.green = self.green_init = green  # signalisation du feu, rouge ou vert
        self.delay = delay  # durée entre les changements de signalisation

    def __str__(self):
        return f"TrafficLight(id={self.id}, green={self.green}, road={self.road})"

    def update(self, t):
        """Actualise l'état du feu, c'est-à-dire rouge ou vert."""
        if int(t/self.delay) % 2 == 0:
            self.green = self.green_init
        else:
            self.green = not self.green_init

    @property
    def fake_car(self):
        if self.green:
            return None
        else:
            fake_car = Car(0, 0, 1, 1, (0, 0, 0), -2)
            fake_car.d = self.road.length
            return fake_car


class Road:
    def __init__(self, start, end, width, color, car_factory: CarFactory, traffic_light: TrafficLight, obj_id):
        """
        Route droite.

        :param start: coordonnées du début
        :param end: coordonnées de la fin
        :param width: largeur
        :param color: couleur
        :param car_factory: CarFactory
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.road = None
        self.start, self.end = start, end
        self.width = width
        self.color = color

        (startx, starty), (endx, endy) = self.start, self.end
        self.length = length(start, end)
        self.vd = vect_dir(self.start, self.end)  # vecteur directeur de la route, normé
        vnx, vny = vect_norm(self.vd, self.width / 2)  # vecteur normal pour les coord des coins
        self.coins = (startx + vnx, starty + vny), (startx - vnx, starty - vny), (endx - vnx, endy - vny), (
            endx + vnx, endy + vny)
        self.angle = vect_angle(self.vd)

        if car_factory is None:
            self.car_factory = CarFactory()
        else:
            self.car_factory = car_factory

        self.cars: list[Car] = []

        self.car_sorter = CarSorter()

        self.exiting_cars: list[Car] = []

        self.traffic_light: TrafficLight = self.new_traffic_light(traffic_light)

    def __str__(self):
        return f"Road(id={self.id}, length={round(self.length, 2)}, coins={rec_round(self.coins, 2)}, color={self.color})"

    def dist_to_pos(self, d):
        startx, starty = self.start
        vdx, vdy = self.vd
        return startx + vdx * d, starty + vdy * d

    @property
    def arrows_coords(self):
        rarete = s.ARROW_RARETE  # inverse de la fréquence des flèches
        num = round(self.length / rarete)  # nombre de flèches pour la route
        arrows = []
        for i in range(num):
            x, y = self.dist_to_pos((i + 0.5) * rarete)  # "+ O.5" pour centrer les flèches sur la longueur
            arrows.append((x, y, self.angle))
        log(f"{arrows=}", 3)
        return arrows

    def update_cars_coords(self, dt):
        """Bouge les voitures de la route à leurs positions après dt."""
        for index, car in enumerate(self.cars):
            if index > 0:  # pour toutes les voitures sauf la première, donner la voiture devant
                prev_car = self.cars[index - 1]
            else:
                prev_car = self.traffic_light.fake_car

            # mise à jour des vecteurs du mouvement
            car.update_mvt(dt, prev_car)

            # mise à jour de la position
            car.x, car.y = self.dist_to_pos(car.d)

            # mise à jour des coins, pour l'affichage
            car.update_coins(self.vd)

            log(f"Updating {car} of {self}", 3)

            if car.d >= self.length:
                self.exiting_cars.append(car)
                self.cars.remove(car)
                log(f"Removing {car} of {self}", 2)

    def new_car(self, car: Car):  # TODO: ajouter car au mileu de la route
        car.road = self
        vnx, vny = vect_norm(self.vd, car.width / 2)  # vecteur normal pour les coord des coins
        sx, sy = self.start
        ex, ey = self.dist_to_pos(car.length)
        car.coins = (sx + vnx, sy + vny), (sx - vnx, sy - vny), (ex - vnx, ey - vny), (ex + vnx, ey + vny)
        car.x, car.y = self.start
        car.d = 0
        self.cars.append(car)
        log(f"Creating {car} on road {self}", 2)

    def new_traffic_light(self, tl: TrafficLight):
        if tl is None:
            return TrafficLight(green=True, delay=float("+inf"))

        tl.road = self
        vnx, vny = vect_norm(self.vd, self.width/2)
        x1, y1 = self.dist_to_pos(self.length)
        x2, y2 = self.dist_to_pos(self.length - tl.width)
        tl.coins = (x1 + vnx, y1 + vny), (x1 - vnx, y1 - vny), (x2 - vnx, y2 - vny), (x2 + vnx, y2 + vny)
        log(f"Creating {tl} on road {self}", 2)
        return tl
