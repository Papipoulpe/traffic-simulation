import pandas as pd

from .math_and_util import *


class Car:
    def __init__(self, v: float = s.CAR_V, a: float = s.CAR_A, length: float = s.CAR_LENGTH, width: float = s.CAR_WIDTH,
                 a_max: float = s.A_MAX, a_min: float = s.A_MIN, t_react: float = s.T_REACT,
                 color: Couleur = s.CAR_COLOR, obj_id: Optional[int] = None, **kwargs):
        """
        Voiture.

        :param v: vitesse, en m/s
        :param a: accélération, en m/s²
        :param length: longueur, en m
        :param width: largeur, en m
        :param a_max: accélération maximale, en m/s²
        :param a_min: déccélération minimale, en m/s² (a priori négative)
        :param t_react: temps de réaction du conducteur, en s
        :param color: couleur
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id, pos=kwargs.get("pos_id", True))
        self.color = color
        self.length = length * s.SCALE
        self.width = width * s.SCALE
        self.road = None  # actuelle route auquel le véhicule est rattaché
        self.next_road = None  # prochaine route du véhicule, définie par le CarSorter de self.road
        self.simulation = get_by_id(0)

        self._d = 0  # distance du centre du véhicule depuis le début de la route
        self.total_d = 0  # distance totale parcourue par la voiture
        self._pos = npz(2)  # position du centre du véhicule
        self.v = v * s.SCALE if v is not None else None # vitesse
        self.a = a * s.SCALE  # acceleration

        # historiques de la distance parcourue, vitesse et accélération de la voiture en fonction du temps
        self.d_t = {}
        self.v_t = {}
        self.a_t = {}

        # paramètres de l'IDM
        self.delta_d_min = s.DELTA_D_MIN * s.SCALE  # commun à tous les véhicules
        self.a_max = a_max * s.SCALE
        self.a_min = a_min * s.SCALE
        self.a_exp = s.A_EXP  # commun à tous les véhicules
        self.t_react = t_react
        self.v_max = ...  # défini par la route dans road.new_car()

        # coordonnées des coins du rectangle représentant la voiture, pour affichage
        self.vertices = npz((4, 2))

        # coordonnées des coins du trapèze à l'avant de la voiture, pour détecter les collisions
        self.front_bumper_hitbox = npz((4, 2))

        # coordonnées des coins du rectangle sur les côtés et l'arrière de la voiture, pour détecter les collisions
        self.side_bumper_hurtbox = npz((4, 2))

        self.leaders = []  # leaders de la voiture
        self.bumping_cars = []  # voitures en collision avec la voiture

    def __repr__(self):
        return f"Car(id={self.id}, road.id={self.road.id}, pos={self.pos}, d={self.d}, v={self.v}, a={self.a}, v_max={self.v_max}, coins={rec_round(self.vertices)}, virtual_leader={self.virtual_leader}, bumping_cars={self.bumping_cars}, leaders={self.leaders}, next_road={self.next_road}, color={closest_color(self.color)})"

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, d):
        """car.d.setter : quand car.d est mis à jour, cette fonction est exécutée et met à jour la distance totale
        parcourue et l'historique de cette distance en fonction du temps par la même occasion."""
        self.total_d += d - self._d
        self._d = d
        self.d_t[round(self.simulation.t, 4)] = self.total_d/s.SCALE

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        """car.pos.setter : quand car.pos est mis à jour, cette fonction est exécutée est met à jour les coins pour
        l'affichage et les coins des zones de collision par la même occasion."""
        self._pos = pos

        vd = self.road.vd  # on récupère le vecteur directeur de la route
        vd_l = vd * self.length / 2  # on le norme pour la longueur de la voiture
        vn_w = normal_vector(
            self.road.vd,
            self.width / 2)  # vecteur normal de la route normé pour la largeur de la voiture
        vn_ddm = normal_vector(
            self.road.vd,
            self.delta_d_min / 2)  # vn de la route normé pour la distance de sécurité

        # coins d'affichage
        c1 = self.pos + vn_w - vd_l  # derrière droit
        c2 = self.pos - vn_w - vd_l  # derrière gauche
        c3 = self.pos - vn_w + vd_l  # devant gauche
        c4 = self.pos + vn_w + vd_l  # devant droit
        self.vertices = c1, c2, c3, c4

        # coins de la zone de collision devant
        vd_ddmp = vd * (self.delta_d_min + self.v + self.t_react) / 2  # vecteur directeur de la route normé pour la distance de sécurité et la vitesse de la voiture
        c1 = self.pos + vn_w + vd_l + vd_ddmp  # devant droit
        c2 = self.pos - vn_w + vd_l + vd_ddmp  # devant gauche
        c3 = self.pos - vn_w - vn_ddm + vd_l  # derrière gauche
        c4 = self.pos + vn_w + vn_ddm + vd_l  # derrière droit
        self.front_bumper_hitbox = c1, c2, c3, c4

        # coins de la zone de collision autour
        vd_ddm = vd * self.delta_d_min / 2  # vecteur directeur de la route normé pour la distance de sécurité
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
        leader_coords = self.virtual_leader  # récupération du leader virtuel

        if s.USE_IDM:
            self.a = iidm(self, leader_coords)  # si l'IDM est utilisé, on met à jour l'accélération

        update_taylor(self, dt)  # mise à jour de d et v par développement de Taylor

        self.v_t[round(self.simulation.t, 4)] = self.a/s.SCALE  # mise à jour de l'historique des vitesses
        self.a_t[round(self.simulation.t, 4)] = self.v/s.SCALE  # et des accélérations

    def is_bumping_with(self, other_car: "Car"):
        """Renvoie si la voiture **percute** ``other_car``, c'est-à-dire si ``car.front_bumper_hitbox``  et
        ``other_car.side_bumper_hurtbox`` se superposent. Pour des questions de rapidité, cette fonction ne vérifie
        pas la superposition stricte mais seulement si certains point de ``car.front_bumper_hitbox`` sont à
        l'intérieur de ``other_car.side_bumper_hurtbox``."""
        # on vérifie d'abord une condition nécessaire mais pas suffisante, moins coûteuses en calcul, qui est
        # l'appartenance du point other_car.pos au cercle de centre car.pos et de rayon
        # (longueur de other_car) + (longueur de car) + (longueur de la zone de collision de devant)
        radius = self.pos, other_car.length + self.length + self.delta_d_min + self.v + self.t_react
        if not is_inside_circle(other_car.pos, radius):
            return False

        # on regarde si chaque coin de la zone de collision de devant de car est dans celle de derrière de other_car
        for c in self.front_bumper_hitbox:
            if is_inside_rectangle(c, other_car.side_bumper_hurtbox):
                return True

        # puis on regarde pour des points au milieu de ces coins
        dvd, dvg, drg, drd = self.front_bumper_hitbox

        if is_inside_rectangle((dvd + drd)/2, other_car.side_bumper_hurtbox):
            return True

        if is_inside_rectangle((dvg + drg)/2, other_car.side_bumper_hurtbox):
            return True

        return False

    @property
    def virtual_leader(self):
        """Renvoie la distance au et la vitesse d'un leader virtuel de la voiture, i.e. un couple (d, v) où :

        - si la voiture est en prévision de collision avec d'autres voitures, c'est-à-dire si ``car.bumping_cars``
        n'est pas vide, alors d est la moyenne des distances à vol d'oiseau entre la voiture et les voitures de
        ``car.bumping_cars`` et v est la moyenne de leurs vitesses projetées selon le vecteur directeur de la route

        - sinon, d est la moyenne des distances par la route jusqu'aux voitures de ``car.leaders`` et v la moyenne de
        leurs vitesses."""
        if self.bumping_cars:
            leader_coords = npz(2)
            for other_car in self.bumping_cars:
                d = max(distance(self.pos, other_car.pos) - self.length / 2 - other_car.length / 2, 0)
                v = other_car.v * (self.road.vd @ other_car.road.vd)
                leader_coords += npa([d, v])
            return leader_coords / len(self.bumping_cars)

        elif self.leaders:
            leader_coords = npz(2)
            for other_car, d in self.leaders:
                leader_coords += npa([d, other_car.v])
            return leader_coords / len(self.leaders)

        else:
            return None


class CarFactory:
    def __init__(self, freq=None, crea=None, obj_id=None):
        """
        Création de voitures à l'entrée d'une route.

        :param freq: fréquence de création de voiture, peut être de type ``[a, b]`` pour une pause aléatoire d'une durée entre a et b secondes entre la création de deux voiture, ``a`` pour une fréquence constante ou une fonction f(t) -> bool
        :param crea: manière de choisir la voiture à créer, peut être de type ``"{'arg': val, ...}"``, ``"rand_color"``, ``"rand_length"`` et/ou ``"rand_width"``, une fonction f(t) -> Car ou vide pour la voiture par défaut
        """
        self.id = new_id(self, obj_id)

        self.road = ...
        self.next_t = ...  # éventuelement utilisé pour fréquence aléatoire

        self.freq_func = self.init_freqfunc(freq)  # définit dans road.init_car_factory()
        self.crea_func = self.init_creafunc(crea)  # définit dans road.init_car_factory()

    def __repr__(self):
        return f"CarFactory(id={self.id})"

    def init_freqfunc(self, arg):
        """Génère une fonction de fréquence de création."""
        if isinstance(arg, (int, float)) or (isinstance(arg, (tuple, list)) and arg[0] == arg[1]):
            # si de type a ou [a, a], renvoie True toutes les a secondes
            if isinstance(arg, (list, tuple)):
                a = arg[0]
            else:
                a = arg

            def freq_func(t):
                right_time = round(t, 2) % a == 0
                if self.road.cars and not s.CAR_FACT_FORCE_CREA:
                    last_car = self.road.cars[-1]
                    space_available = last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                    return right_time and space_available
                else:
                    return right_time

            return freq_func

        elif isinstance(arg, (tuple, list)):
            # si de type [a, b], attendre aléatoirement entre a et b secondes
            self.next_t = np.random.uniform(arg[0], arg[1])

            def freq_func(t):
                if t >= self.next_t:
                    delay = np.random.uniform(arg[0], arg[1])
                    self.next_t = t + delay
                    if self.road.cars and not s.CAR_FACT_FORCE_CREA:
                        last_car = self.road.cars[-1]
                        space_available = last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                        return space_available
                    else:
                        return True
                else:
                    return False

            return freq_func
        elif arg is None:
            return None
        else:  # si une fonction du temps est fournie
            def freq_func(t):
                right_time = arg(t)
                if self.road.cars and not s.CAR_FACT_FORCE_CREA:
                    last_car = self.road.cars[-1]
                    space_available = last_car.d > last_car.length + s.DELTA_D_MIN  # s'il y a de la place disponible ou non
                    return right_time and space_available
                else:
                    return right_time

            return freq_func

    @staticmethod
    def init_creafunc(arg):
        """Génère une fonction de création."""
        if not isinstance(arg, (str, list, type(None))):
            return arg

        if isinstance(arg, str):
            arg = [arg]

        attrs = {}

        def crea_func(*_, **__):
            if arg is None:
                return Car(**attrs)

            if "rand_color" in arg:
                attrs["color"] = [np.random.randint(s.CAR_RAND_COLOR_MIN, s.CAR_RAND_COLOR_MAX) for _ in range(3)]
            if "rand_length" in arg:
                attrs["length"] = np.random.randint(s.CAR_RAND_LENGTH_MIN, s.CAR_RAND_LENGTH_MAX)
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

    def factory(self, args_fact: dict, args_crea: dict):
        """
        Renvoie une voiture générée par la fonction de création si la fonction de fréquence de création l'autorise.

        :param args_fact: dictionnaire d'arguments pour la fonction de fréquence de création
        :param args_crea: dictionnaire d'arguments pour la fonction de création
        """
        # si une fonction de fréquence de création est définie et qu'elle autorise la création
        if self.freq_func is not None and self.freq_func(**args_fact):
            # on renvoie la voiture créée par la fonction de création
            return self.crea_func(**args_crea)


class CarSorter:
    def __init__(self, method=None, obj_id=None):
        """
        Gestion des voitures à la sortie d'une route, en fait décidé dès l'entrée de la voiture sur la route.

        :param method: dictionnaire associant un id de route à une probabilité ou ``None``
        """
        self.id = new_id(self, obj_id)

        # si la méthode est un dictionnaire non vide associant une route à une proba
        if isinstance(method, dict) and method:
            self.method = "probs"
            probs, roads = [], []
            for road in method:
                probs.append(method[road])
                roads.append(road)

            def sort_func():
                return get_by_id(np.random.choice(roads, p=probs))

        else:  # si la méthode est None ou un disctionnaire vide, les voitures seront supprimées
            self.method = None
            sort_func = empty_function

        self.sort_func = sort_func

    def __repr__(self):
        return f"CarSorter(id={self.id}, method={self.method})"

    def sorter(self):
        return self.sort_func()


class TrafficLight:
    def __init__(self, state_init: int, static=False, obj_id: int = None):
        """
        Feu tricolore de signalisation.

        :param state_init: état initial du feu : 0 = rouge, 1 = orange, 2 = vert
        :param static: si le feu change d'état pendant la simulation
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self._road: Road = ...  # route auquelle le feu est rattaché
        self.pos = npz(2)  # position
        self.coins = npz((4, 2))  # coins pour affichage
        self.width = s.TL_WIDTH  # épaisseur du trait représentant le feu

        self.state = self.state_init = state_init  # signalisation du feu : rouge 0, orange 1 ou vert 2
        self.static = static  # si le feu change d'état durant la simulation

        self.dummy_cars = {}  # fausses voitures du feu, définies dans traffic_light.road.setter

    def __repr__(self):
        return f"TrafficLight(id={self.id}, state={self.state}, state_init={self.state_init}, static={self.static})"

    @property
    def road(self):
        return self._road

    @road.setter
    def road(self, road):
        """traffic_light.road.setter : quand traffic_light.road est mis à jour, cette fonction est exécutée et met à
        jour la postion, les coins d'affichage et les fausses voitures du feu par la même occasion."""
        self._road = road

        self.pos = road.dist_to_pos(road.length - self.width/2)

        vd = self.road.vd * s.TL_WIDTH / 2
        vn = normal_vector(vd, self.road.width / 2)
        self.coins = self.pos - vd + vn, self.pos - vd - vn, self.pos + vd - vn, self.pos + vd + vn

        dummy_car_red = Car(v=0, length=0, pos_id=False)
        dummy_car_red._d = self.road.length  # contourne car.d.setter
        dummy_car_orange = Car(v=0, length=0, pos_id=False)
        dummy_car_orange._d = self.road.length + s.DELTA_D_MIN / s.TL_ORANGE_SLOW_DOWN_COEFF  # contourne car.d.setter
        dummy_car_red._pos = dummy_car_orange._pos = self.pos  # contourne car.pos.setter
        self.dummy_cars = {0: dummy_car_red, 1: dummy_car_orange}  # dictionnaire qui à l'état du feu associe la faussse voiture

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
        return self.dummy_cars.get(self.state)


class StopSign:
    def __init__(self, obj_id: int = None):
        """
        Panneau de signalisation Stop.

        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.pos = npz(2)
        self.coins = npz((4, 2))
        self._road = ...
        self.dummy_car = ...

    def __repr__(self):
        return f"StopSign(id={self.id})"

    @property
    def road(self):
        return self._road

    @road.setter
    def road(self, road):
        """stop_sign.road.setter : quand stop_sign.road est mis à jour, cette fonction est exécutée et met à jour la
        postion, les coins d'affichage et la fausse voiture du panneau stop par la même occasion."""
        self._road = road
        self.pos = road.dist_to_pos(road.length)

        vd = self.road.vd * s.SS_WIDTH / 2
        vn = normal_vector(vd, self.road.width / 2)
        self.coins = self.pos - vd, self.pos - vn, self.pos + vd, self.pos + vn

        dummy_car = Car(v=0, length=0, pos_id=False)
        dummy_car._d = road.length + 2.5 * s.DELTA_D_MIN
        dummy_car._pos = self.pos
        self.dummy_car = dummy_car


class Sensor:
    def __init__(self, position: float = 1, attributes_to_monitor: Optional[str] | Sequence[Optional[str]] = ("v", "a"),
                 obj_id=None):
        """
        Capteur qui récupère des données de la simulation.

        :param position: pourcentage de la route où sera placé le capteur
        :param attributes_to_monitor: les attributs des voitures à surveiller, en chaînes de caractères : None pour juste compter le nombre de voitures, ou autant que voulu parmi ``v``, ``a``, ``length``, ``width``, ``color`` et ``total_d`` ou parmi ``d(t)``, ``v(t)`` et ``a(t)``
        """
        self.id = new_id(self, obj_id)
        self.position = position
        self.corners = npz((4, 2))

        self.data = []
        self.data_is_vals = True  # si le capteur récupère les valeurs instantantées des attributs des voitures ou l'historique de ces valeurs
        self.already_seen_cars_id = []
        self.attributes_to_monitor = self.init_atm(attributes_to_monitor)

        self.road = None
        self._d = 0

    def __repr__(self):
        return f"Sensor(id={self.id}, position={self.position}, attributes_to_monitor={self.attributes_to_monitor})"

    def init_atm(self, atm):
        if atm is None:
            return []
        elif isinstance(atm, str):
            atm = [atm]
        if any(arg in atm for arg in ["d(t)", "v(t)", "a(t)"]):
            self.data_is_vals = False
        else:
            self.data_is_vals = True
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
        atm_with_units = [f"{attr} ({UNITS_OF_ATTR[attr]})" for attr in self.attributes_to_monitor]

        if self.data_is_vals:
            return pd.DataFrame(data=self.data, columns=["t (s)", "car_id"] + atm_with_units)

        else:
            multi_index = pd.MultiIndex.from_product([self.already_seen_cars_id, atm_with_units], names=["car_id", "f(t)"])
            data = []
            dt = get_by_id(0).dt
            t_max = max(data_t for data_t, *_ in self.data)
            t = 0

            while t <= t_max:
                row = []
                for data_row in self.data:
                    _, _, *time_to_val_dics = data_row
                    for time_to_val_dic in time_to_val_dics:
                        val = time_to_val_dic.get(round(t, 4))
                        row.append(val)
                t += dt
                data.append(row)

            index = []
            t = 0
            while t <= t_max:
                index.append(round(t, 4))
                t += dt

            return pd.DataFrame(data=data, columns=multi_index, index=index)

    def watch_car(self, car, t):
        data_row = [t, car.id]
        for attr in self.attributes_to_monitor:
            real_attr = {"d(t)": "d_t", "v(t)": "v_t", "a(t)": "a_t"}.get(attr, attr)
            val = car.__getattribute__(real_attr)
            if "m" in UNITS_OF_ATTR[attr] and isinstance(val, (int, float)):
                val /= s.SCALE  # si l'attribut a une longueur dans ses unités, on la remet à l'échelle
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
        if x == "t" and not self.data_is_vals:
            x = None
        if isinstance(x, str):
            x += f" ({UNITS_OF_ATTR.get(x, '')})"

        df = self.df
        df.loc[:, df.columns != "car_id"].plot(x=x)


class Road:
    def __init__(self, start, end, width, color, v_max, with_arrows, car_factory, sign, sensors, obj_id):
        """
        Route droite.

        :param start: coordonnées du début
        :param end: coordonnées de la fin
        :param width: largeur
        :param color: couleur
        :param v_max: limite de vitesse de la route
        :param with_arrows: si des flèches seront affichées sur la route ou non
        :param car_factory: éventuelle CarFactory
        :param sign: éventuel élément de signalisation : feu de signalisation ou panneau stop
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.start, self.end = npa((start, end))
        self.width = width
        self.color = color
        self.with_arrows = with_arrows

        self.length = distance(self.start, self.end)  # longueur de la route
        self.vd = direction_vector(self.start, self.end)  # vecteur directeur de la route, normé
        vn = normal_vector(self.vd, self.width / 2)  # vecteur normal pour les coord des coins
        self.coins = self.start + vn, self.start - vn, self.end - vn, self.end + vn  # coordonnées des coins, pour l'affichage
        self.angle = angle_of_vect(self.vd)  # angle de la route par rapport à l'axe des abscisses

        self.cars: list[Car] = []  # liste des voitures appartenant à la route
        self.v_max = v_max  # vitesse limite de la route

        self.car_sorter = CarSorter()
        self.car_factory = self.init_car_factory(car_factory)
        self.arrows_coords = self.init_arrows_coords()
        self.sign = self.init_sign(sign)
        self.sensors = self.init_sensors(sensors)

    def __repr__(self):
        return f"Road(id={self.id}, start={self.start}, end={self.end}, length={self.length}, vd={self.vd}, color={closest_color(self.color)})"

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

    def init_car_factory(self, car_factory):
        if car_factory is None:
            cf = CarFactory()
            cf.road = self
            return cf
        else:
            car_factory.road = self
            return car_factory

    def init_sign(self, sign):
        """Initialise l'élément de signalisation de la route."""
        if sign is None:
            return TrafficLight(state_init=2, static=True)
        else:
            sign.road = self  # sign.road.setter gère tout
            return sign

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
        sign_car = self.sign.dummy_car  # on récupère la fausse voiture du feu/stop de la route

        for index, car in enumerate(self.cars):
            if index > 0:  # pour toutes les voitures sauf la première, donner la voiture devant
                leading_car = self.cars[index - 1]
                car.leaders = [(leading_car, leading_car.d - leading_car.length/2 - car.d - car.length/2)]
            elif sign_car is not None:  # si la fausse voiture n'est pas None, on l'utilise pour la première voiture
                leading_car = sign_car
                car.leaders = [(leading_car, leading_car.d - leading_car.length/2 - car.d - car.length/2)]
            else:  # sinon pour la première voiture, donner la prochaine voiture
                car.leaders = [(leader, self.length - car.d - car.length/2 + d) for leader, d in leaders]

            # mise à jour des vecteurs du mouvement
            car.update(dt)

            # transition douce du v_max avec celui de la prochaine route
            car.v_max = self.v_max_transition(car)

            # mise à jour de la position et des coins d'affichage
            car.pos = self.dist_to_pos(car.d)

            if car.d > self.length:  # si la voiture sort de la route
                car.d -= self.length  # on initialise le prochain d
                if car.next_road is not None:
                    car.next_road.new_car(car)  # on l'ajoute à la prochaine route si elle existe
                self.cars.remove(car)  # on retire la voiture de la liste des voitures (pas d'impact sur la boucle avec enumerate)

    def update_sensors(self, t):
        for sensor in self.sensors:
            sensor.watch_road(t)

    def update_sign(self, t):
        """Met à jour la signalétique de la route (feu/stop) si besoin."""
        if isinstance(self.sign, TrafficLight):
            self.sign.update(t)

    def new_car(self, car: Car):
        """Ajoute une voiture à la route, qui conservera son ``car.d``."""
        if car is None:
            return
        car.next_road = self.car_sorter.sorter()  # récupération de la prochaine route de la voiture
        if car.d > self.length:  # si la voiture sort (déjà !) de la route
            car.d -= self.length  # on initialise le prochain d
            if car.next_road is not None:
                car.next_road.new_car(car)  # on l'ajoute à la prochaine route si elle existe
            return
        car.road = self
        car.v_max = self.v_max
        if car.v is None:
            car.v = self.v_max
        car.pos = self.dist_to_pos(car.d)
        self.cars.append(car)

    def v_max_transition(self, car: Car):
        if isinstance(self, SRoad):
            return car.v_max

        elif car.next_road is not None and car.d >= self.length * (1 - s.ROAD_TRANSITION_SIZE):
            alpha = (car.d - self.length * (1 - s.ROAD_TRANSITION_SIZE)) / (self.length * s.ROAD_TRANSITION_SIZE)
            v_max1 = self.v_max
            v_max2 = car.next_road.v_max
            return alpha * v_max2 + (1 - alpha) * v_max1

        else:
            return car.v_max


class SRoad(Road):
    def __init__(self, start, end, width, color, v_max, obj_id):
        """Sous-route droite composant ArcRoad, dérivant de Road."""
        super().__init__(start, end, width, color, v_max, False, None, None, None, obj_id)

    def __repr__(self):
        return "S" + super().__repr__()


class ArcRoad:
    def __init__(self, start, end, vdstart, vdend, v_max, n, width, color, car_factory, obj_id):
        """
        Route courbée, composée de multiples routes droites.

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
        self.v_max = v_max*s.ARCROAD_SLOW_COEFF

        self.car_factory = self.init_car_factory(car_factory)
        self.sign, self.update_sign = None, empty_function
        self.sensors, self.update_sensors = [], empty_function

        intersec = lines_intersection(start, vdstart, end, vdend)
        self.points = bezier_curve(self.start, intersec, self.end, n + 1)  # n + 1 points pour n routes
        self.length = sum(distance(self.points[i], self.points[i + 1]) for i in range(n))

        self.sroads = []
        self.sroad_end_to_arcroad_end = {}
        for i in range(n):
            rstart = self.points[i]
            rend = self.points[i + 1]
            sroad = SRoad(rstart, rend, width, color, self.v_max, None)
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
        # parcours des sroads à l'envers pour ne pas actualiser une même voiture plusieurs fois
        for i in range(self.n - 1, -1, -1):
            if leaders is None:
                # s'il n'y a pas de voitures après la route
                self.sroads[i].update_cars(dt, None)
            else:
                # s'il en a, on les donne avec le bon d pour chaque route
                d_ajusted_leaders = [(leader, d + (i + 1) * self.sroads[i].length) for leader, d in leaders]
                self.sroads[i].update_cars(dt, d_ajusted_leaders)

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
