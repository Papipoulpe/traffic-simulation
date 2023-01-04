from maths_and_utils import *
import settings as s


class CarFactory:
    def __init__(self, crea_func=None, fact_func=None, obj_id=None):
        """
        Création de voitures à l'entrée d'une route.

        :param fact_func: fréquence de création de voiture, peut être de type [a, b] pour une pause aléatoire entre la création de deux voiture, a pour une fréquence constante ou une fonction
        :param crea_func: manière de choisir la voiture à créer, peut être de type "{'arg': val}", "rand_color", "rand_length" et/ou "rand_width", une fonction ou vide pour la voiture par défaut
        """
        self.id = new_id(self, obj_id)

        self.next_t = 0  # éventuelement utilisé pour fréquence aléatoire

        if isinstance(crea_func, (str, list, type(None))):  # si crea_func n'est pas une fonction
            self.crea_func = self.generic_creafunc(crea_func)  # on génère une fonction de création
        else:
            self.crea_func = crea_func

        if isinstance(fact_func, (list, float, int)):  # si fact_func n'est pas une fonction
            self.fact_func = self.generic_factfunc(fact_func)  # on génère une fonction de fréquence de création
        else:
            self.fact_func = fact_func

    def __repr__(self):
        return f"CarFactory(id={self.id})"

    def factory(self, args_crea, args_fact):
        """
        :param args_crea: arguments de la fonction de création
        :param args_fact: arguments de la fonction de fréquence de création
        """
        if self.fact_func and self.fact_func(**args_fact):  # si une fonction de fréquence est définie et qu'elle autorise la création
            return self.crea_func(**args_crea)  # on renvoie la voiture créée par la fonction de création

    @staticmethod
    def generic_creafunc(func_name):
        """Génère une fonction de création."""
        if isinstance(func_name, str):
            func_name = [func_name]

        attrs = {"v": s.CAR_V, "a": s.CAR_A, "color": s.CAR_COLOR, "width": s.CAR_WIDTH, "le": s.CAR_LENGTH, "obj_id": None}

        def crea_func(*_, **__):
            if "rand_color" in func_name:
                attrs["color"] = [np.random.randint(s.CAR_RAND_COLOR_MIN, s.CAR_RAND_COLOR_MAX) for _ in range(3)]
            if "rand_length" in func_name:
                attrs["le"] = np.random.randint(s.CAR_RAND_LENGTH_MIN, s.CAR_RAND_LENGTH_MAX)
            if "rand_width" in func_name:
                attrs["width"] = np.random.randint(s.CAR_RAND_WIDTH_MIN, s.CAR_RAND_WIDTH_MAX)
            try:
                attrs_dic = parse(func_name[0])
            except ValueError:
                attrs_dic = {}
            for key in attrs_dic:
                attrs[key] = attrs_dic[key]
            return Car(**attrs)

        return crea_func

    def generic_factfunc(self, func_name):
        """Génère une fonction de fréquence de création."""
        if isinstance(func_name, (int, float)) or func_name[0] == func_name[1]:
            # si func_name est de type a ou [a, a], renvoie True toutes les a secondes
            if isinstance(func_name, (list, tuple)):
                a = func_name[0]
            else:
                a = func_name

            def fact_func(t, last_car):
                place_dispo = last_car is None or last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                bon_moment = round(t, 2) % a == 0
                return bon_moment and place_dispo
            return fact_func
        else:
            # sinon, de type [a, b], attend aléatoirement entre a et b secondes
            def fact_func(t, last_car):
                if t >= self.next_t:
                    delay = np.random.uniform(func_name[0], func_name[1])
                    self.next_t = t + delay
                    place_dispo = last_car is None or last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                    return place_dispo
            return fact_func


class CarSorter:
    def __init__(self, method=None, obj_id=None):
        """
        Gestion des voitures à la sortie d'une route.

        :param method: dictionnaire associant une probabilité à une autre route, fonction ou None
        """
        self.id = new_id(self, obj_id)

        if isinstance(method, dict):  # si la méthode est un dictionnaire associant une proba à une route
            self.method = "probs"
            probs, roads = [], []
            for p in method:
                probs.append(method[p])
                roads.append(p)

            def sort_func(*_, **__):
                return ids[np.random.choice(roads, p=probs)]

        elif method is None:  # si la méthode est None, les voitures seront supprimées
            self.method = None
            sort_func = empty_function

        else:  # si la méthode est une fonction
            self.method = "func"
            sort_func = method

        self.sort_func = sort_func

    def __repr__(self):
        return f"CarSorter(id={self.id}, method={self.method})"

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
        self.road = None

        self.d = 0  # distance du derrière depuis le début de la route
        self.x, self.y = 0, 0  # position du mileu du derrière dans la fenêtre
        self.v = v  # vitesse
        self.a = a  # acceleration

        self.delta_d_min = s.DELTA_D_MIN  # pour l'IDM
        self.a_max = s.A_MAX
        self.a_min = s.A_MIN
        self.a_exp = s.A_EXP
        self.t_react = s.T_REACT

        self.coins = ((0, 0), (0, 0), (0, 0), (0, 0))  # coordonnées des coins, pour affichage

    def __repr__(self):
        return f"Car(id={self.id}, x={self.x}, y={self.y}, d={self.d}, v={self.v}, a={self.a}, coins={rec_round(self.coins)}, color={closest_colour(self.color)})"

    def update_mvt(self, dt, avg_leading_car_coords):
        """
        Actualise les coordonnées du mouvement (position, vitesse, accéleration) de la voiture.

        :param dt: durée du mouvement
        :param avg_leading_car_coords: distance et vitesse d'une éventuelle voiture devant
        """

        idm(self, avg_leading_car_coords, dt)

    def update_coins(self):
        """Actualise les coins selon la position."""
        vdx, vdy = self.road.vd
        vnx, vny = vect_norm(self.road.vd, self.width / 2)
        c1 = self.x + vnx - self.length * vdx / 2, self.y + vny - self.length * vdy / 2
        c2 = self.x - vnx - self.length * vdx / 2, self.y - vny - self.length * vdy / 2
        c3 = self.x - vnx + self.length * vdx / 2, self.y - vny + self.length * vdy / 2
        c4 = self.x + vnx + self.length * vdx / 2, self.y + vny + self.length * vdy / 2
        self.coins = c1, c2, c3, c4


class TrafficLight:
    def __init__(self, state_init: int, static=False, obj_id: int = None):
        self.id = new_id(self, obj_id)
        self.road: Road = ...  # route auquel le feu est rattaché
        self.coins = (0, 0), (0, 0), (0, 0), (0, 0)  # coins pour affichage
        self.width = s.TL_WIDTH

        self.state = self.state_init = state_init  # signalisation du feu : rouge 0, orange 1 ou vert 2
        self.static = static

    def __repr__(self):
        return f"TrafficLight(id={self.id}, state={self.state}, state_init={self.state_init}, static={self.static})"

    def update(self, t):
        """Actualise l'état du feu, c'est-à-dire rouge ou vert."""
        if self.static:
            return
        state_init_delay = {0: s.TL_GREEN_DELAY + s.TL_ORANGE_DELAY,
                            1: s.TL_GREEN_DELAY,
                            2: 0}[self.state_init]
        t2 = (t + state_init_delay) % (s.TL_RED_DELAY + s.TL_ORANGE_DELAY + s.TL_GREEN_DELAY)
        if 0 <= t2 < s.TL_GREEN_DELAY:
            self.state = 2
        elif s.TL_GREEN_DELAY <= t2 < s.TL_GREEN_DELAY + s.TL_ORANGE_DELAY:
            self.state = 1
        else:
            self.state = 0

    @property
    def fake_car(self):
        """Renvoie une fausse voiture, qui fera ralentir la première voiture de la route selon la couleur du feu."""
        if self.state == 0:  # si feu rouge
            fake_car = Car(0, 0, 0, 0, (0, 0, 0), None)
            fake_car.d = self.road.length + s.DELTA_D_MIN
            fake_car.road = self.road
        elif self.state == 1:  # si feu orange
            fake_car = Car(0, 0, 0, 0, (0, 0, 0), None)
            fake_car.d = self.road.length + s.DELTA_D_MIN/s.TL_ORANGE_SLOW_DOWN_COEFF
            fake_car.road = self.road
        else:  # si feu vert
            fake_car = None
        return fake_car


class Road:
    def __init__(self, start, end, width, color, with_arrows, car_factory, traffic_light, obj_id):
        """
        Route droite.

        :param start: coordonnées du début
        :param end: coordonnées de la fin
        :param width: largeur
        :param color: couleur
        :param with_arrows: si des flèches seront affichées sur la route ou non
        :param car_factory: éventuelle CarFactory
        :param traffic_light: éventuel feu de signalisation
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.start, self.end = start, end
        self.width = width
        self.color = color
        self.with_arrows = with_arrows

        (startx, starty), (endx, endy) = self.start, self.end
        self.length = length(start, end)
        self.vd = vect_dir(self.start, self.end)  # vecteur directeur de la route, normé
        vnx, vny = vect_norm(self.vd, self.width / 2)  # vecteur normal pour les coord des coins
        self.coins = (startx + vnx, starty + vny), (startx - vnx, starty - vny), (endx - vnx, endy - vny), (
            endx + vnx, endy + vny)  # coordonnées des coins, pour l'affichage
        self.angle = angle_of_vect(self.vd)  # angle de la route par rapport à l'axe des abscisses

        if car_factory is None:
            self.car_factory = CarFactory()
        else:
            self.car_factory = car_factory

        self.cars: list[Car] = []  # liste des voitures appartenant à la route
        self.v_max = s.V_MAX  # vitesse limite de la route

        self.car_sorter = CarSorter()

        self.exiting_cars: list[Car] = []  # liste des voitures quittant la route

        self.traffic_light: TrafficLight = self.new_traffic_light(traffic_light)

    def __repr__(self):
        return f"Road(id={self.id}, start={self.start}, end={self.end}, color={closest_colour(self.color)})"

    def dist_to_pos(self, d):
        """Renvoie les coordonnées d'un objet à une distance ``d`` du début le la route."""
        startx, starty = self.start
        vdx, vdy = self.vd
        return startx + vdx * d, starty + vdy * d

    @property
    def arrows_coords(self):
        """Renvoie les coordonnées des flèches de la route."""
        if not self.with_arrows:
            return []
        rarete = s.ARROW_RARETE  # inverse de la fréquence des flèches
        num = round(self.length / rarete)  # nombre de flèches pour la route
        arrows = []
        for i in range(num):
            x, y = self.dist_to_pos((i + 0.5) * rarete)  # "+ O.5" pour centrer les flèches sur la longueur
            arrows.append((x, y, self.angle))
        return arrows

    def update_cars(self, dt, leader_coords):
        """
        Bouge les voitures de la route à leurs positions après dt.

        :param dt: durée du mouvement
        :param leader_coords: distance et vitesse de la voiture leader
        """
        for index, car in enumerate(self.cars):
            if index > 0:  # pour toutes les voitures sauf la première, donner la voiture devant
                leading_car = self.cars[index - 1]
                leading_car_coords = leading_car.d, leading_car.v
            elif self.traffic_light.fake_car:  # si le feu est rouge, donner la fake_car du feu
                leading_car = self.traffic_light.fake_car
                leading_car_coords = leading_car.d, leading_car.v
            elif leader_coords is not None:  # sinon pour la première voiture, donner la prochaine voiture
                leading_car_coords = leader_coords[0] + self.length, leader_coords[1]
            else:
                leading_car_coords = None

            # mise à jour des vecteurs du mouvement
            car.update_mvt(dt, leading_car_coords)

            # mise à jour de la position
            car.x, car.y = self.dist_to_pos(car.d)

            # mise à jour des coins, pour l'affichage
            car.update_coins()

            if car.d >= self.length:
                self.exiting_cars.append(car)
                self.cars.remove(car)

    def new_car(self, car: Car):
        if car is None:
            return
        car.road = self
        car.x, car.y = self.dist_to_pos(0)
        car.d = 0
        car.update_coins()
        self.cars.append(car)

    def new_traffic_light(self, tl: TrafficLight):
        if tl is None:
            return TrafficLight(state_init=2, static=True)
        tl.road = self
        vnx, vny = vect_norm(self.vd, self.width/2)
        x1, y1 = self.dist_to_pos(self.length)
        x2, y2 = self.dist_to_pos(self.length - tl.width)
        tl.coins = (x1 + vnx, y1 + vny), (x1 - vnx, y1 - vny), (x2 - vnx, y2 - vny), (x2 + vnx, y2 + vny)
        return tl


class SRoad(Road):
    def __init__(self, start, end, width, color, obj_id):
        """Sous-route droite composant ArcRoad, dérivant de Road."""
        super().__init__(start, end, width, color, False, None, None, obj_id)


class ArcRoad:
    def __init__(self, start, end, vdstart, vdend, n, width, color, car_factory, obj_id):
        """
        Route courbée.

        :param start: coordonnées du début
        :param end: coordonnées de la fin
        :param vdstart: vecteur directeur de la droite asymptote au début
        :param vdend: vecteur directeur de la droite asymptote à la fin
        :param n: nombre de routes droites formant la route courbée
        :param width: largeur
        :param color: couleur
        :param car_factory: éventuelle CarFactory
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.start, self.end = start, end
        self.width = width
        self.color = color
        self.length = 0

        intersec = intersection_droites(start, vdstart, end, vdend)
        self.points = courbe_bezier(start, intersec, end, n)
        self.sroads = []
        for i in range(len(self.points) - 1):
            rstart = self.points[i]
            rend = self.points[i + 1]
            road = SRoad(rstart, rend, width, color, -(s.ARCROAD_N*self.id+i))
            road.v_max *= s.ARCROAD_V_MAX_COEFF
            self.sroads.append(road)
            self.length += road.length

        self.exiting_cars: list[Car] = []

        if car_factory is None:
            self.car_factory = CarFactory()
        else:
            self.car_factory = car_factory

        self.car_sorter = CarSorter()

        self.cars = []  # listes des voitures appartenant à la routes

        self.traffic_light = None

    def __repr__(self):
        return f"ArcRoad(id={self.id}, start={self.start}, end={self.end}, color={closest_colour(self.color)}, length={self.length}, sroads={self.sroads})"

    def update_cars(self, dt, leader_coords):
        for index, sroad in enumerate(self.sroads):
            sroad.update_cars(dt, leader_coords)

            if index == len(self.sroads) - 1:  # si dernière sroad
                self.exiting_cars = sroad.exiting_cars
                for car in self.exiting_cars:
                    self.cars.remove(car)
            else:
                next_road = self.sroads[index + 1]

                for car in sroad.exiting_cars:
                    next_road.new_car(car)  # on ajoute la voiture à la sroad suivante

            sroad.exiting_cars = []

    def new_car(self, car):
        if car is None:
            return
        self.sroads[0].new_car(car)
        self.cars.append(car)
