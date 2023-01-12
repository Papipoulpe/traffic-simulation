from .maths_and_utils import *
import trafficsimulation.settings as s


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
        Gestion des voitures à la sortie d'une route, en fait décidé dès l'entrée de la voiture sur la route.

        :param method: dictionnaire associant un id de route à une probabilité ou None
        """
        self.id = new_id(self, obj_id)

        if isinstance(method, dict):  # si la méthode est un dictionnaire associant une proba à une route
            self.method = "probs"
            probs, roads = [], []
            for p in method:
                probs.append(method[p])
                roads.append(p)

            def sort_func():
                return get_by_id(np.random.choice(roads, p=probs))

        else:  # si la méthode est None, les voitures seront supprimées
            self.method = None
            sort_func = empty_function

        self.sort_func = sort_func

    def __repr__(self):
        return f"CarSorter(id={self.id}, method={self.method})"

    def sorter(self):
        return self.sort_func()


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
        self.next_road = None

        self.d = 0  # distance du derrière depuis le début de la route
        self.x, self.y = 0, 0  # position du mileu du derrière dans la fenêtre
        self.v = v  # vitesse
        self.a = a  # acceleration

        self.delta_d_min = s.DELTA_D_MIN  # pour l'IDM
        self.a_max = s.A_MAX  # pour l'IDM
        self.a_min = s.A_MIN  # pour l'IDM
        self.a_exp = s.A_EXP  # pour l'IDM
        self.t_react = s.T_REACT  # pour l'IDM

        self.corners = ((0, 0), (0, 0), (0, 0), (0, 0))  # coordonnées des coins du rectangle représentant la voiture, pour affichage
        self.front_bumper_hitbox = ((0, 0), (0, 0), (0, 0), (0, 0))  # coordonnées des coins du rectangle à l'avant de la voiture, pour détecter les collisions
        self.side_bumper_hurtbox = ((0, 0), (0, 0), (0, 0), (0, 0))  # coordonnées des coins du rectangle sur les côtés et l'arrière de la voiture, pour détecter les collisions

        self.bumping_cars = []  # autres voitures avec lesquelles elle est en collision

    def __repr__(self):
        return f"Car(id={self.id}, x={self.x}, y={self.y}, d={self.d}, v={self.v}, a={self.a}, next_road={self.next_road}, coins={rec_round(self.corners)}, bumping_cars={self.bumping_cars}, color={closest_color(self.color)})"

    def update(self, dt, leader_coords):
        """
        Actualise les coordonnées du mouvement (position, vitesse, accéleration) de la voiture.

        :param dt: durée du mouvement
        :param leader_coords: distance et vitesse d'une éventuelle voiture devant
        """
        if self.bumping_cars:
            n = len(self.bumping_cars)
            d_avg = sum(car.d for car in self.bumping_cars)/n
            v_avg = sum(car.v for car in self.bumping_cars)/n
            leader_coords = d_avg, v_avg

        idm(self, leader_coords, dt)

    def update_corners(self):
        """Actualise les coins de la voiture (d'affichage et de collision) selon sa position."""
        vdx, vdy = self.road.vd  # on récupère le vecteur directeur de la route
        vdx_l = vdx * self.length / 2  # on le norme pour la longueur de la voiture
        vdy_l = vdy * self.length / 2
        vdx_ddm = vdx * self.delta_d_min / 4  # on le norme pour la distance de sécurité
        vdy_ddm = vdy * self.delta_d_min / 4
        vnx_w, vny_w = vect_norm(self.road.vd, self.width / 2)  # vecteur normal de la route normé pour la largeur de la voiture
        vnx_ddm, vny_ddm = vect_norm(self.road.vd, self.delta_d_min / 2)  # vn normé pour la distance de sécurité
        
        # coins d'affichage
        c1 = self.x + vnx_w - vdx_l, self.y + vny_w - vdy_l
        c2 = self.x - vnx_w - vdx_l, self.y - vny_w - vdy_l
        c3 = self.x - vnx_w + vdx_l, self.y - vny_w + vdy_l
        c4 = self.x + vnx_w + vdx_l, self.y + vny_w + vdy_l
        self.corners = c1, c2, c3, c4

        # points de collision de devant
        c1 = self.x - vnx_w - 0 + vdx_l + 2*vdx_ddm, self.y - vny_w - 0 + vdy_l + 2*vdy_ddm
        c2 = self.x + vnx_w + 0 + vdx_l + 2*vdx_ddm, self.y + vny_w + 0 + vdy_l + 2*vdy_ddm
        c3 = self.x + vnx_w + vnx_ddm + vdx_l, self.y + vny_w + vny_ddm + vdy_l
        c4 = self.x - vnx_w - vnx_ddm + vdx_l, self.y - vny_w - vny_ddm + vdy_l
        self.front_bumper_hitbox = c1, c2, c3, c4

        # coins de la zone de collision autour
        c1 = self.x + vnx_w + vnx_ddm - vdx_l - vdx_ddm, self.y + vny_w + vny_ddm - vdy_l - vdy_ddm
        c2 = self.x - vnx_w - vnx_ddm - vdx_l - vdx_ddm, self.y - vny_w - vny_ddm - vdy_l - vdy_ddm
        c3 = self.x - vnx_w - vnx_ddm + vdx_l, self.y - vny_w - vny_ddm + vdy_l
        c4 = self.x + vnx_w + vnx_ddm + vdx_l, self.y + vny_w + vny_ddm + vdy_l
        self.side_bumper_hurtbox = c1, c2, c3, c4
        
    def is_bumping_with(self, other_car: "Car"):
        """Renvoie si la voiture rentre en collision **sur** ``other_car``, c'est-à-dire si un des coins de
        ``car.front_bumper_points`` est à l'intérieur de ``other_car.side_bumper_corners``."""
        res = any(is_inside_rectangle(corner, other_car.side_bumper_hurtbox) for corner in self.front_bumper_hitbox)
        return res


class TrafficLight:
    def __init__(self, state_init: int, static=False, obj_id: int = None):
        """Feux de signalisation."""
        self.id = new_id(self, obj_id)
        self.road: Road = ...  # route auquel le feu est rattaché
        self.coins = (0, 0), (0, 0), (0, 0), (0, 0)  # coins pour affichage
        self.width = s.TL_WIDTH

        self.state = self.state_init = state_init  # signalisation du feu : rouge 0, orange 1 ou vert 2
        self.static = static

    def __repr__(self):
        return f"TrafficLight(id={self.id}, state={self.state}, state_init={self.state_init}, static={self.static})"

    def update(self, t):
        """Actualise l'état du feu, c'est-à-dire rouge, orange ou vert."""
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

        self.traffic_light: TrafficLight = self.new_traffic_light(traffic_light)

    def __repr__(self):
        return f"Road(id={self.id}, start={self.start}, end={self.end}, color={closest_color(self.color)})"

    def __eq__(self, other_car):
        return self.id == other_car.id

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
        rarete = s.ROAD_ARROW_PERIOD  # inverse de la fréquence des flèches
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
            car.update(dt, leading_car_coords)

            # mise à jour de la position
            car.x, car.y = self.dist_to_pos(car.d)

            # mise à jour des coins, pour l'affichage
            car.update_corners()

            if car.d >= self.length:  # si la voiture sort de la route
                car.d -= self.length  # on initialise le prochain d
                if car.next_road is not None:
                    car.next_road.new_car(car)  # on l'ajoute à la prochaine route si elle existe
                self.cars.remove(car)  # on retire la voiture de la liste des voitures (pas d'impact sur la boucle avec enumerate)

    def new_car(self, car: Car):
        if car is None:
            return
        car.road = self
        car.next_road = self.car_sorter.sorter()
        car.x, car.y = self.dist_to_pos(car.d)
        car.update_corners()
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
        self.n = n

        intersec = intersection_droites(start, vdstart, end, vdend)
        self.points = bezier_curve(start, intersec, end, n)
        self.sroads = []
        self.sroad_end_to_arcroad_end = {}
        for i in range(n):
            rstart = self.points[i]
            rend = self.points[i + 1]
            sroad = SRoad(rstart, rend, width, color, -(n*self.id+i))
            sroad.v_max *= s.ARCROAD_V_MAX_COEFF
            self.sroads.append(sroad)
            self.length += sroad.length

        for index, sroad in enumerate(self.sroads):
            if index < n - 1:
                sroad.car_sorter = CarSorter(method={self.sroads[index + 1].id: 1})

        if car_factory is None:
            self.car_factory = CarFactory()
        else:
            self.car_factory = car_factory

        self.traffic_light = None

    def __repr__(self):
        return f"ArcRoad(id={self.id}, start={self.start}, end={self.end}, color={closest_color(self.color)}, length={self.length}, sroads={self.sroads})"

    @property
    def cars(self):
        car_list = []
        for sroad in self.sroads:
            car_list += sroad.cars
        return car_list

    def update_cars(self, dt, leader_coords):
        for index, sroad in enumerate(self.sroads):
            if leader_coords is None:
                sroad.update_cars(dt, None)
            else:
                leader_d, leader_v = leader_coords
                leader_d += (self.n - index)*sroad.length
                sroad.update_cars(dt, (leader_d, leader_v))

    @property
    def car_sorter(self):
        return self.sroads[-1].car_sorter

    @car_sorter.setter
    def car_sorter(self, car_sorter):
        self.sroads[-1].car_sorter = car_sorter

    def new_car(self, car):
        if car is None:
            return
        self.sroads[0].new_car(car)
