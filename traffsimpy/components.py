from .math_and_util import *


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

        self._d = 0  # distance du derrière depuis le début de la route
        self.total_d = 0  # distance totale parcourue par la voiture
        self._pos = npz(2)  # position du mileu du derrière dans la fenêtre
        self.v = v  # vitesse
        self.a = a  # acceleration

        self.delta_d_min = s.DELTA_D_MIN  # pour l'IDM
        self.a_max = s.A_MAX  # pour l'IDM
        self.a_min = s.A_MIN  # pour l'IDM
        self.a_exp = s.A_EXP  # pour l'IDM
        self.t_react = s.T_REACT  # pour l'IDM

        self.corners = npz((4, 2))  # coordonnées des coins du rectangle représentant la voiture, pour affichage
        self.front_bumper_hitbox = npz(
            (4, 2))  # coordonnées des coins du rectangle à l'avant de la voiture, pour détecter les collisions
        self.side_bumper_hurtbox = npz((4,
                                        2))  # coordonnées des coins du rectangle sur les côtés et l'arrière de la voiture, pour détecter les collisions

        self.leaders = []  # leaders de la voitures

    def __repr__(self):
        return f"Car(id={self.id}, pos={self.pos}, d={self.d}, v={self.v}, a={self.a}, coins={rec_round(self.corners)}, virtual_leader={self.virtual_leader}, leaders={self.leaders}, next_road={self.next_road}, color={closest_color(self.color)})"

    def __eq__(self, other):
        return self.id == other.id

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, d):
        self.total_d += d - self._d
        self._d = d

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos

        vd = self.road.vd  # on récupère le vecteur directeur de la route
        vd_l = vd * self.length / 2  # on le norme pour la longueur de la voiture
        vd_ddm = vd * self.delta_d_min / 2  # on le norme pour la distance de sécurité
        vd_ddmp = vd * (
                    self.delta_d_min + self.v + self.t_react) / 2  # on le norme pour la distance de sécurité et la vitesse
        vn_w = normal_vector(
            self.road.vd,
            self.width / 2)  # vecteur normal de la route normé pour la largeur de la voiture
        vn_ddm = normal_vector(
            self.road.vd,
            self.delta_d_min / 2)  # vn normé pour la distance de sécurité

        # coins d'affichage
        c1 = self.pos + vn_w - vd_l  # derrière droit
        c2 = self.pos - vn_w - vd_l  # derrière gauche
        c3 = self.pos - vn_w + vd_l  # devant gauche
        c4 = self.pos + vn_w + vd_l  # devant droit
        self.corners = c1, c2, c3, c4

        # coins de la zone de collision de devant
        c1 = self.pos + vn_w + vd_l + vd_ddmp  # devant droit
        c2 = self.pos - vn_w + vd_l + vd_ddmp  # devant gauche
        c3 = self.pos - vn_w - vn_ddm + vd_l  # derrière gauche
        c4 = self.pos + vn_w + vn_ddm + vd_l  # derrière droit
        self.front_bumper_hitbox = c1, c2, c3, c4

        # coins de la zone de collision autour
        c1 = self.pos + vn_w + vn_ddm - vd_l - vd_ddm  # derrière droit
        c2 = self.pos - vn_w - vn_ddm - vd_l - vd_ddm  # derrière gauche
        c3 = self.pos - vn_w - vn_ddm + vd_l  # devant gauche
        c4 = self.pos + vn_w + vn_ddm + vd_l  # devant droit
        self.side_bumper_hurtbox = c1, c2, c3, c4

    def update(self, dt):
        """
        Actualise les coordonnées du mouvement (position, vitesse, accéleration) de la voiture.

        :param dt: durée du mouvement
        """
        leader_coords = self.virtual_leader

        idm(self, leader_coords, dt)

    def is_bumping_with(self, other_car: "Car"):
        """Renvoie si la voiture **percute** ``other_car``, c'est-à-dire si un des coins de
        ``car.front_bumper_hitbox`` est à l'intérieur de ``other_car.side_bumper_hurtbox``."""
        return any(is_inside_rectangle(corner, other_car.side_bumper_hurtbox) for corner in self.front_bumper_hitbox)

    @property
    def virtual_leader(self):
        """Renvoie la distance au et la vitesse du leader virtuel de la voiture, qui prend en compte les prochaines voitures et les voitures avec lesquelle elle est en collision."""
        if not self.leaders:
            return None

        leader_coords = npz(2)
        total_imp = 0

        for other_car, d, importance in self.leaders:
            leader_coords += npa([d, other_car.v]) * importance
            total_imp += importance

        return leader_coords / total_imp


class CarFactory:
    def __init__(self, crea_func=None, fact_func=None, obj_id=None):
        """
        Création de voitures à l'entrée d'une route.

        :param fact_func: fréquence de création de voiture, peut être de type ``[a, b]`` pour une pause aléatoire entre la création de deux voiture, ``a`` pour une fréquence constante ou une fonction
        :param crea_func: manière de choisir la voiture à créer, peut être de type ``"{'arg': val}"``, ``"rand_color"``, ``"rand_length"`` et/ou ``"rand_width"``, une fonction ou vide pour la voiture par défaut
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
        if self.fact_func and self.fact_func(
                **args_fact):  # si une fonction de fréquence est définie et qu'elle autorise la création
            return self.crea_func(**args_crea)  # on renvoie la voiture créée par la fonction de création

    @staticmethod
    def generic_creafunc(arg):
        """Génère une fonction de création."""
        if isinstance(arg, str):
            arg = [arg]

        attrs = {"v":      s.CAR_V, "a": s.CAR_A, "color": s.CAR_COLOR, "width": s.CAR_WIDTH, "le": s.CAR_LENGTH,
                 "obj_id": None}

        def crea_func(*_, **__):
            if arg is None:
                return Car(**attrs)

            if "rand_color" in arg:
                attrs["color"] = [np.random.randint(s.CAR_RAND_COLOR_MIN, s.CAR_RAND_COLOR_MAX) for _ in range(3)]
            if "rand_length" in arg:
                attrs["le"] = np.random.randint(s.CAR_RAND_LENGTH_MIN, s.CAR_RAND_LENGTH_MAX)
            if "rand_width" in arg:
                attrs["width"] = np.random.randint(s.CAR_RAND_WIDTH_MIN, s.CAR_RAND_WIDTH_MAX)
            try:
                attrs_dic = parse(arg[0])
            except ValueError:
                attrs_dic = {}
            for key in attrs_dic:
                attrs[key] = attrs_dic[key]
            return Car(**attrs)

        return crea_func

    def generic_factfunc(self, arg):
        """Génère une fonction de fréquence de création."""
        if isinstance(arg, (int, float)) or arg[0] == arg[1]:
            # si func_name est de type a ou [a, a], renvoie True toutes les a secondes
            if isinstance(arg, (list, tuple)):
                a = arg[0]
            else:
                a = arg

            def fact_func(t, last_car):
                space_available = last_car is None or last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                right_time = round(t, 2) % a == 0
                return right_time and (space_available or s.CAR_FACT_FORCE_CREA)

            return fact_func
        else:
            # sinon, de type [a, b], attend aléatoirement entre a et b secondes
            def fact_func(t, last_car):
                if t >= self.next_t:
                    delay = np.random.uniform(arg[0], arg[1])
                    self.next_t = t + delay
                    space_available = last_car is None or last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                    return space_available or s.CAR_FACT_FORCE_CREA
                else:
                    return False

            return fact_func


class CarSorter:
    def __init__(self, method=None, obj_id=None):
        """
        Gestion des voitures à la sortie d'une route, en fait décidé dès l'entrée de la voiture sur la route.

        :param method: dictionnaire associant un id de route à une probabilité ou ``None``
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


class TrafficLight:
    def __init__(self, state_init: int, static=False, obj_id: int = None):
        """Feux de signalisation."""
        self.id = new_id(self, obj_id)
        self.road: Road = ...  # route auquel le feu est rattaché
        self.coins = npz((4, 2))  # coins pour affichage
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
    def dummy_car(self):
        """Renvoie une fausse voiture, qui fera ralentir la première voiture de la route selon la couleur du feu."""
        if self.state == 0:  # si feu rouge
            fake_car = Car(0, 0, 0, 0, (0, 0, 0), None)
            fake_car.d = self.road.length + s.DELTA_D_MIN
            fake_car.road = self.road
        elif self.state == 1:  # si feu orange
            fake_car = Car(0, 0, 0, 0, (0, 0, 0), None)
            fake_car.d = self.road.length + s.DELTA_D_MIN / s.TL_ORANGE_SLOW_DOWN_COEFF
            fake_car.road = self.road
        else:  # si feu vert
            fake_car = None
        return fake_car


class Sensor:
    def __init__(self, position: float = 1, attributes_to_monitor: Optional[str] | Sequence[Optional[str]] = ("v", "a"),
                 obj_id=None):
        """
        Capteur qui récupère des données de la simulation.

        :param position: pourcentage de la route où sera placé le capteur
        :param attributes_to_monitor: les attributs des voitures à surveiller, en chaînes de caractères,  parmi ``v``, ``a``, ``length``, ``width``, ``color`` et ``total_d``
        """
        self.id = new_id(self, obj_id)
        self.attributes_to_monitor = self.init_atm(attributes_to_monitor)
        self.position = position
        self.corners = npz((4, 2))

        self.data = []
        self.already_seen_cars_id = []

        self.road = None
        self._d = 0

    def __repr__(self):
        return f"Sensor(id={self.id}, position={self.position}, attributes_to_monitor={self.attributes_to_monitor})"

    @staticmethod
    def init_atm(atm):
        if isinstance(atm, str):
            return [atm]
        elif atm is None:
            return []
        else:
            return list(atm)

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, d):
        self._d = d
        vn_w = normal_vector(self.road.vd, self.road.width / 2)
        vd = self.road.vd
        vd_l = vd * s.SENSOR_WIDTH / 2
        pos = self.road.dist_to_pos(self._d)
        c1 = pos + vn_w - vd_l
        c2 = pos - vn_w - vd_l
        c3 = pos - vn_w + vd_l
        c4 = pos + vn_w + vd_l
        self.corners = c1, c2, c3, c4

    @property
    def df(self):
        return data_frame(data=self.data, columns=["t", "car_id"] + self.attributes_to_monitor)

    def watch_car(self, car, t):
        data_row = [t, car.id]
        for attr in self.attributes_to_monitor:
            val = car.__getattribute__(attr)
            if attr in ["v", "a", "width", "length"]:
                val /= s.SCALE
            data_row.append(val)
        self.data.append(data_row)
        self.already_seen_cars_id.append(car.id)

    def watch_road(self, t):
        for car in self.road.cars:
            if car.id not in self.already_seen_cars_id and car.d >= self.d:
                self.watch_car(car, t)

    @property
    def results(self):
        return str(pd.concat([self.df, self.df.describe()]))

    def export(self, file_path, sheet_name, describe):
        if describe:
            pd.concat([self.df, self.df.describe()]).to_excel(file_path, sheet_name)
        else:
            self.df.to_excel(file_path, sheet_name)

    def plot(self, x="t"):
        df = self.df
        df.loc[:, df.columns != "car_id"].plot(x=x)


class Road:
    def __init__(self, start, end, width, color, v_max, with_arrows, car_factory, traffic_light, sensors, obj_id):
        """
        Route droite.

        :param start: coordonnées du début
        :param end: coordonnées de la fin
        :param width: largeur
        :param color: couleur
        :param v_max: limite de vitesse de la route
        :param with_arrows: si des flèches seront affichées sur la route ou non
        :param car_factory: éventuelle CarFactory
        :param traffic_light: éventuel feu de signalisation
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.start, self.end = npa((start, end))
        self.width = width
        self.color = color
        self.with_arrows = with_arrows

        self.length = length(self.start, self.end)
        self.vd = direction_vector(self.start, self.end)  # vecteur directeur de la route, normé
        vn = normal_vector(self.vd, self.width / 2)  # vecteur normal pour les coord des coins
        self.coins = self.start + vn, self.start - vn, self.end - vn, self.end + vn  # coordonnées des coins, pour l'affichage
        self.angle = angle_of_vect(self.vd)  # angle de la route par rapport à l'axe des abscisses

        self.cars: list[Car] = []  # liste des voitures appartenant à la route
        self.v_max = v_max  # vitesse limite de la route

        self.car_sorter = CarSorter()
        self.car_factory = self.init_car_factory(car_factory)
        self.arrows_coords = self.init_arrows_coords()
        self.traffic_light = self.init_traffic_light(traffic_light)
        self.sensors = self.init_sensors(sensors)

    def __repr__(self):
        return f"Road(id={self.id}, start={self.start}, end={self.end}, vd={self.vd}, color={closest_color(self.color)})"

    def __eq__(self, other):
        return self.id == other.id

    def init_arrows_coords(self):
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

    @staticmethod
    def init_car_factory(car_factory):
        if car_factory is None:
            return CarFactory()
        else:
            return car_factory

    def init_traffic_light(self, traffic_light):
        """Initialise le feu de signalisation de la route."""
        if traffic_light is None:
            return TrafficLight(state_init=2, static=True)
        else:
            traffic_light.road = self
            vnx, vny = normal_vector(self.vd, self.width / 2)
            x1, y1 = self.dist_to_pos(self.length)
            x2, y2 = self.dist_to_pos(self.length - traffic_light.width)
            traffic_light.coins = (x1 + vnx, y1 + vny), (x1 - vnx, y1 - vny), (x2 - vnx, y2 - vny), (x2 + vnx, y2 + vny)
            return traffic_light

    def init_sensors(self, sensors):
        if isinstance(sensors, Sensor):
            sensors = [sensors]
        elif sensors is None:
            sensors = []

        for sensor in sensors:
            sensor.road = self
            sensor.d = self.length * sensor.position / 100

        return sensors

    def dist_to_pos(self, d):
        """Renvoie les coordonnées d'un objet de la route à une distance ``d`` du début de la route."""
        return self.start + self.vd * d

    def update_cars(self, dt, leaders):
        """
        Bouge les voitures de la route à leurs positions après dt.

        :param dt: durée du mouvement
        :param leaders: voitures leaders de la première voiture de la route
        """
        for index, car in enumerate(self.cars):
            if index > 0:  # pour toutes les voitures sauf la première, donner la voiture devant
                leading_car = self.cars[index - 1]
                car.leaders += [(leading_car, leading_car.d - car.d, s.CAR_LEADERS_COEFF_IN_FRONT_CAR)]
            elif self.traffic_light.dummy_car:  # si le feu est rouge, donner la fake_car du feu
                leading_car = self.traffic_light.dummy_car
                car.leaders += [(leading_car, leading_car.d - car.d, s.CAR_LEADERS_COEFF_IN_FRONT_CAR)]
            elif leaders:  # sinon pour la première voiture, donner la prochaine voiture
                car.leaders += [(leader, self.length - car.d + d, importance) for leader, d, importance in leaders]

            # mise à jour des vecteurs du mouvement
            car.update(dt)

            # mise à jour de la position et des coins d'affichage
            car.pos = self.dist_to_pos(car.d)

            if car.d >= self.length:  # si la voiture sort de la route
                car.d -= self.length  # on initialise le prochain d
                if car.next_road is not None:
                    car.next_road.new_car(car)  # on l'ajoute à la prochaine route si elle existe
                self.cars.remove(
                    car)  # on retire la voiture de la liste des voitures (pas d'impact sur la boucle avec enumerate)

    def update_sensors(self, t):
        for sensor in self.sensors:
            sensor.watch_road(t)

    def update_traffic_light(self, t):
        if self.traffic_light is not None:
            self.traffic_light.update(t)

    def new_car(self, car: Car):
        """Ajoute une voiture à la route, qui conservera son ``car.d``."""
        if car is None:
            return
        car.road = self
        car.next_road = self.car_sorter.sorter()
        car.pos = self.dist_to_pos(car.d)
        self.cars.append(car)


class SRoad(Road):
    def __init__(self, start, end, width, color, v_max, obj_id):
        """Sous-route droite composant ArcRoad, dérivant de Road."""
        super().__init__(start, end, width, color, v_max, False, None, None, None, obj_id)


class ArcRoad:
    def __init__(self, start, end, vdstart, vdend, v_max, n, width, color, car_factory, obj_id):
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
        self.start, self.end = npa((start, end))
        self.width = width
        self.color = color
        self.length = 0
        self.n = n

        self.car_factory = self.init_car_factory(car_factory)
        self.traffic_light, self.update_traffic_light = None, empty_function
        self.sensors, self.update_sensors = [], empty_function

        intersec = intersection_droites(start, vdstart, end, vdend)
        self.points = bezier_curve(self.start, intersec, self.end, n)
        sroad_length = length(self.points[0], self.points[1])
        self.length = sroad_length * n

        self.sroads = []
        self.sroad_end_to_arcroad_end = {}
        for i in range(n):
            rstart = self.points[i]
            rend = self.points[i + 1]
            sroad = SRoad(rstart, rend, width, color, v_max * s.ARCROAD_V_MAX_COEFF, -(n * self.id + i))
            self.sroads.append(sroad)

        for index, sroad in enumerate(self.sroads):
            if index < n - 1:
                sroad.car_sorter = CarSorter(method={self.sroads[index + 1].id: 1})

    def __repr__(self):
        return f"ArcRoad(id={self.id}, start={self.start}, end={self.end}, color={closest_color(self.color)}, length={self.length}, sroads={self.sroads})"

    def __eq__(self, other):
        return self.id == other.id

    @staticmethod
    def init_car_factory(car_factory):
        if car_factory is None:
            return CarFactory()
        else:
            return car_factory

    @property
    def cars(self):
        car_list = []
        for sroad in self.sroads:
            car_list += sroad.cars
        return car_list

    def update_cars(self, dt, leaders):
        for index, sroad in enumerate(self.sroads):
            if leaders is None:
                sroad.update_cars(dt, None)
            else:
                nleaders = [(leader, d + (self.n - index) * sroad.length, i) for leader, d, i in leaders]
                sroad.update_cars(dt, nleaders)

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
