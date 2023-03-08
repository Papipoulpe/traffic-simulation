import pandas as pd

from .math_and_util import *


class Car:
    def __init__(self, v: float = sc.car_v, a: float = sc.car_a, length: float = sc.car_length, width: float = sc.car_width,
                 a_max: float = sc.a_max, a_min: float = sc.a_min, t_react: float = sc.t_react,
                 color: Couleur = sc.car_color, obj_id: Optional[int] = None, **kwargs):
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
        self.length = length * sc.scale
        self.width = width * sc.scale
        self.road = ...  # actuelle route à laquelle le véhicule est rattaché, définie dans road.new_car()
        self.next_road = ...  # prochaine route du véhicule, définie par le CarSorter de self.road

        self._d = 0  # distance du centre du véhicule depuis le début de la route
        self.total_d = 0  # distance totale parcourue par la voiture
        self._pos = npz(2)  # position du centre du véhicule
        self.v = v * sc.scale if v is not None else None  # vitesse
        self.a = a * sc.scale  # acceleration

        # historiques de la distance parcourue, vitesse et accélération de la voiture en fonction du temps
        self.d_t = {}
        self.v_t = {}
        self.a_t = {}

        # paramètres de l'IDM
        self.delta_d_min = sc.delta_d_min * sc.scale  # commun à tous les véhicules
        self.a_max = a_max * sc.scale
        self.a_min = a_min * sc.scale
        self.a_exp = sc.a_exp  # commun à tous les véhicules
        self.t_react = t_react
        self.v_max = ...  # défini par la route dans road.new_car()

        # coordonnées des sommets du rectangle représentant la voiture, pour affichage
        self.vertices = npz((4, 2))

        # coordonnées des sommets du trapèze à l'avant de la voiture, pour détecter les collisions
        self.front_bumper_hitbox = npz((4, 2))

        # coordonnées des sommets du rectangle sur les côtés et l'arrière de la voiture, pour détecter les collisions
        self.side_bumper_hurtbox = npz((4, 2))

        # coordonnées des sommets inférieur gauche et supérieur droite de la boite englobante droite (AABB)
        self.aabb = npz((2, 2))

        self.leaders = []  # leaders de la voiture
        self.soon_colliding_cars = []  # voitures en potentielle collision avec la voiture

    def __repr__(self):
        return f"Car(id={self.id}, pos={self.pos}, d={self.d}, v={self.v}, a={self.a}, v_max={self.v_max}, virtual_leader={self.virtual_leader}, soon_colliding_cars={self.soon_colliding_cars}, leaders={self.leaders}, next_road={self.next_road}, color={closest_color(self.color)})"

    @property
    def d(self):
        return self._d

    @d.setter
    def d(self, d):
        """car.d.setter : quand car.d est mis à jour, cette fonction est exécutée et met à jour la distance totale
        parcourue et l'historique de cette distance en fonction du temps par la même occasion."""
        self.total_d += d - self._d
        self._d = d
        self.d_t[round(self.road.simulation.t, 4)] = self.total_d / sc.scale

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        """car.pos.setter : quand car.pos est mis à jour, cette fonction est exécutée est met à jour les sommets pour
        l'affichage et les sommets des zones de collision par la même occasion."""
        self._pos = pos

        vd = self.road.vd  # on récupère le vecteur directeur de la route
        vd_l = vd * self.length / 2  # on le norme pour la longueur de la voiture
        vn_w = normal_vector(
            self.road.vd,
            self.width / 2)  # vecteur normal de la route normé pour la largeur de la voiture
        vn_ddm = normal_vector(
            self.road.vd,
            self.delta_d_min / 2)  # vn de la route normé pour la distance de sécurité

        # sommets d'affichage
        c1 = self.pos + vn_w - vd_l  # derrière droit
        c2 = self.pos - vn_w - vd_l  # derrière gauche
        c3 = self.pos - vn_w + vd_l  # devant gauche
        c4 = self.pos + vn_w + vd_l  # devant droit
        self.vertices = c1, c2, c3, c4

        # sommets de la zone de collision devant
        vd_ddmp = vd * (self.delta_d_min/2 + self.v * self.t_react)  # vecteur directeur de la route normé pour la distance de sécurité et la vitesse de la voiture
        c1 = self.pos + vn_w + vd_l + vd_ddmp  # devant droit
        c2 = self.pos - vn_w + vd_l + vd_ddmp  # devant gauche
        c3 = self.pos - vn_w - vn_ddm + vd_l  # derrière gauche
        c4 = self.pos + vn_w + vn_ddm + vd_l  # derrière droit
        self.front_bumper_hitbox = c1, c2, c3, c4

        # sommets de la zone de collision autour
        vd_ddm = vd * self.delta_d_min / 2  # vecteur directeur de la route normé pour la distance de sécurité
        c1 = self.pos + vn_w + vn_ddm - vd_l - vd_ddm  # derrière droit
        c2 = self.pos - vn_w - vn_ddm - vd_l - vd_ddm  # derrière gauche
        c3 = self.pos - vn_w - vn_ddm + vd_l  # devant gauche
        c4 = self.pos + vn_w + vn_ddm + vd_l  # devant droit
        self.side_bumper_hurtbox = c1, c2, c3, c4

        # sommets inférieur gauche et supérieur droite de l'AABB, pour la 1re phase de recherche de collisions
        c5 = c3 + vd_ddmp
        c6 = c4 + vd_ddmp
        self.aabb = np.min([c1, c2, c5, c6], axis=0), np.max([c1, c2, c5, c6], axis=0)

    def update(self, dt):
        """
        Actualise les coordonnées du mouvement (position, vitesse, accéleration) de la voiture.

        :param dt: durée du mouvement
        """
        leader_coords = self.virtual_leader  # récupération du leader virtuel

        if sc.use_idm:
            self.a = iidm(self, leader_coords)  # si l'IDM est utilisé, on met à jour l'accélération

        update_taylor(self, dt)  # mise à jour de d et v par développement de Taylor

        self.v_t[round(self.road.simulation.t, 4)] = self.a / sc.scale  # mise à jour de l'historique des vitesses
        self.a_t[round(self.road.simulation.t, 4)] = self.v / sc.scale  # et des accélérations

    def may_collide_with(self, other_car: "Car"):
        """Renvoie si la voiture va **percuter** ``other_car``, c'est-à-dire si ``car.front_bumper_hitbox``  et
        ``other_car.side_bumper_hurtbox`` s'intersectent."""
        return do_polygons_intersect(self.front_bumper_hitbox, other_car.side_bumper_hurtbox)

    def might_collide_with(self, other_car: "Car"):
        """Renvoie si la voiture et ``other_car`` vont se rentrer dedans, c'est-à-dire si ``car.front_bumper_hitbox``
        et ``other_car.front_bumper_hitbox`` s'intersectent. Équivalent à
        ``other_car.might_collide_with(car)``."""
        return do_polygons_intersect(self.front_bumper_hitbox, other_car.front_bumper_hitbox)

    def has_priority_over(self, other_car):
        """Renvoie si la voiture est prioritaire devant ``other_car`` dans le cas d'une rencontre. On a pas toujours
        ``car1.has_priority_over(car2) or car2.has_priority_over(car1)``."""
        vd = self.road.vd
        vd_other = other_car.road.vd
        car_other_car_vect = (other_car.pos + vd_other * other_car.length / 2) - (self.pos + vd * self.length / 2)

        # si l'autre voiture est déjà engagée, on est pas prioritaire
        if np.cross(vd, car_other_car_vect) <= 0.5:
            return False

        # si l'une appartient à une route plus prioritaire que l'autre, elle est prioritaire
        if self.road.priority != other_car.road.priority:
            return self.road.priority > other_car.road.priority

        # sinon, on compare leurs directions : si l'autre voiture vient de la gauche de la voiture, on est prioritaire
        return np.cross(vd, vd_other) <= 0

    @property
    def virtual_leader(self):
        """Renvoie la distance au et la vitesse d'un leader virtuel de la voiture, i.e. un couple (d, v) où :

        - si la voiture est en prévision de collision avec d'autres voitures, c'est-à-dire si ``car.bumping_cars``
        n'est pas vide, alors d est la moyenne des distances à vol d'oiseau entre la voiture et les voitures de
        ``car.bumping_cars`` et v est la moyenne de leurs vitesses projetées selon le vecteur directeur de sa route

        - sinon, d est la moyenne des distances par la route jusqu'aux voitures de ``car.leaders`` et v la moyenne de
        leurs vitesses."""
        if self.soon_colliding_cars:
            leader_coords = npz(2)
            for other_car in self.soon_colliding_cars:
                d = max(distance(self.pos, other_car.pos) - self.length / 2 - other_car.length / 2, 0)
                v = other_car.v * (self.road.vd @ other_car.road.vd)
                leader_coords += npa([d, v])
            return leader_coords / len(self.soon_colliding_cars)

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

        :param freq: fréquence de création de voiture, peut être de type ``[a, b]`` pour une pause aléatoire d'une durée entre a et b secondes entre la création de deux voiture, ``a`` pour une fréquence constante, une fonction ``f(t: float) -> bool`` ou vide pour aucune création
        :param crea: manière de choisir la voiture à créer, peut être de type ``{"arg": val, ...}``, ``"rand_color"``, ``"rand_length"`` et/ou ``"rand_width"``, une fonction ``f(t: float) -> Car`` ou vide pour la voiture par défaut
        """
        self.id = new_id(self, obj_id)
        self.road = ...
        self.args = [freq, crea]

        self.next_t = ...  # éventuellement utilisé pour fréquence aléatoire

        self.freq_func = self.init_freqfunc(freq)  # définit dans road.init_car_factory()
        self.crea_func = self.init_creafunc(crea)  # définit dans road.init_car_factory()

    def __repr__(self):
        return f"CarFactory(id={self.id}, freq_arg={self.args[0]}, crea_arg={self.args[1]})"

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
                if self.road.cars and not sc.car_fact_force_crea:
                    last_car = self.road.cars[-1]
                    space_available = last_car.d > last_car.length + sc.delta_d_min  # s'il y a de la place disponible ou non
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
                    if self.road.cars and not sc.car_fact_force_crea:
                        last_car = self.road.cars[-1]
                        space_available = last_car.d > last_car.length + sc.delta_d_min  # s'il y a de la place disponible ou non
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
                if self.road.cars and not sc.CAR_FACT_FORCE_CREA:
                    last_car = self.road.cars[-1]
                    space_available = last_car.d > last_car.length + sc.delta_d_min  # s'il y a de la place disponible ou non
                    return right_time and space_available
                else:
                    return right_time

            return freq_func

    @staticmethod
    def init_creafunc(arg):
        """Génère une fonction de création."""
        if not isinstance(arg, (str, list, dict, type(None))):
            return arg

        if not isinstance(arg, list):
            args = [arg]
        else:
            args = arg

        attrs = {}

        def crea_func(*_, **__):
            if arg is None:
                return Car()

            if "rand_color" in args:
                attrs["color"] = [np.random.randint(sc.car_rand_color_min, sc.car_rand_color_max) for _ in range(3)]

            if "rand_length" in args:
                attrs["length"] = np.random.randint(sc.car_rand_length_min, sc.car_rand_length_max)

            if "rand_width" in args:
                attrs["width"] = np.random.randint(sc.car_rand_width_min, sc.car_rand_width_max)

            for a in args:
                if isinstance(a, dict):
                    for key in a:
                        attrs[key] = a[key]

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

        :param method: id de route, dictionnaire id -> proba, fonction f(t) -> id ou None (voir la doc de simulation.set_road_graph)
        """
        self.id = new_id(self, obj_id)

        self.sorter = self.init_sorter(method)
        self.method = method

    def __repr__(self):
        return f"CarSorter(id={self.id}, method={self.method})"

    def init_sorter(self, method):
        if not method:
            self.method = None
            return empty_function

        elif isinstance(method, int):
            return lambda *_, **__: get_by_id(method)

        elif isinstance(method, dict):
            probs, roads = [], []
            for road in method:
                probs.append(method[road])
                roads.append(road)

            def sort_func(*_, **__):
                return get_by_id(np.random.choice(roads, p=probs))

            return sort_func

        else:
            self.method = "user func"
            return lambda t: get_by_id(method(t))


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
        self.vertices = npz((4, 2))  # sommets pour affichage
        self.width = sc.tl_width  # épaisseur du trait représentant le feu

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
        jour la postion, les sommets d'affichage et les fausses voitures du feu par la même occasion."""
        self._road = road

        self.pos = road.dist_to_pos(road.length - self.width/2)

        vd = self.road.vd * sc.tl_width / 2
        vn = normal_vector(vd, self.road.width / 2)
        self.vertices = self.pos - vd + vn, self.pos - vd - vn, self.pos + vd - vn, self.pos + vd + vn

        dummy_car_red = Car(v=0, length=0, pos_id=False)
        dummy_car_red._d = self.road.length  # contourne car.d.setter
        dummy_car_orange = Car(v=0, length=0, pos_id=False)
        dummy_car_orange._d = self.road.length + sc.delta_d_min / sc.tl_orange_slow_down_coeff  # contourne car.d.setter
        dummy_car_red._pos = dummy_car_orange._pos = self.pos  # contourne car.pos.setter
        self.dummy_cars = {0: dummy_car_red, 1: dummy_car_orange}  # dictionnaire qui à l'état du feu associe la fausse voiture

    def update(self, t):
        """Actualise l'état du feu, c'est-à-dire rouge, orange ou vert."""
        if self.static:
            return

        state_init_delay = {0: sc.tl_green_delay + sc.tl_orange_delay,
                            1: sc.tl_green_delay,
                            2: 0}[self.state_init]
        t2 = (t + state_init_delay) % (sc.tl_red_delay + sc.tl_orange_delay + sc.tl_green_delay)
        if 0 <= t2 < sc.tl_green_delay:
            self.state = 2
        elif sc.tl_green_delay <= t2 < sc.tl_green_delay + sc.tl_orange_delay:
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
        self.vertices = npz((4, 2))
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
        postion, les sommets d'affichage et la fausse voiture du panneau stop par la même occasion."""
        self._road = road
        self.pos = road.dist_to_pos(road.length)

        vd = self.road.vd * sc.ss_width / 2
        vn = normal_vector(vd, self.road.width / 2)
        self.vertices = self.pos - vd, self.pos - vn, self.pos + vd, self.pos + vn

        dummy_car = Car(v=0, length=0, pos_id=False)
        dummy_car._d = road.length + 2.5 * sc.delta_d_min
        dummy_car._pos = self.pos
        self.dummy_car = dummy_car


class Sensor:
    def __init__(self, position: float = 1, attributes_to_monitor: Optional[str] | Sequence[Optional[str]] = ("v", "a"),
                 obj_id=None):
        """
        Capteur qui récupère des données de la simulation.

        :param position: proportion de la route où sera placé le capteur (0 = au tout début, 0.5 = au milieu, 1 = à la toute fin)
        :param attributes_to_monitor: les attributs des voitures à surveiller, en chaînes de caractères : None pour juste compter le nombre de voitures, ou autant que voulu parmi ``v``, ``a``, ``length``, ``width``, ``color`` et ``total_d`` ou parmi ``d(t)``, ``v(t)`` et ``a(t)``
        """
        if not 0 <= position <= 1:
            raise ValueError(f"La position du capteur doit être entre 0 et 1, pas {position}.")

        self.id = new_id(self, obj_id)
        self.d_ratio = position
        self.vertices = npz((4, 2))

        self.data = []
        self.data_is_vals = True  # si le capteur récupère les valeurs instantanées des attributs des voitures ou l'historique de ces valeurs
        self.already_seen_cars_id = []
        self.attributes_to_monitor = self.init_atm(attributes_to_monitor)

        self.road = ...  # route à laquelle le capteur est rattaché, définie dans road.init_sensor()
        self._d = 0  # distance entre le capteur et le début de la route

    def __repr__(self):
        return f"Sensor(id={self.id}, position={self.d_ratio}, attributes_to_monitor={self.attributes_to_monitor})"

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
        vd_l = vd * sc.sensor_width / 2
        pos = self.road.dist_to_pos(self._d)
        c1 = pos + vn_w - vd_l
        c2 = pos - vn_w - vd_l
        c3 = pos - vn_w + vd_l
        c4 = pos + vn_w + vd_l
        self.vertices = c1, c2, c3, c4

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
                val /= sc.scale  # si l'attribut a une longueur dans ses unités, on la remet à l'échelle
            data_row.append(val)
        self.data.append(data_row)
        self.already_seen_cars_id.append(car.id)

    def watch_road(self, t):
        for car in self.road.cars:
            if car.id not in self.already_seen_cars_id and car.d >= self.d:
                self.watch_car(car, t)

    def results(self, form: str = "string", describe: bool = True, **kwargs):
        if describe:
            df = pd.concat([self.df, self.df.describe()])
        else:
            df = self.df

        if form == "str":
            return str(df)

        else:
            return getattr(df, f"to_{form}")(**kwargs)

    def export_results(self, file_path: str, sheet_name: str, describe: bool = True):
        if describe:
            pd.concat([self.df, self.df.describe()]).to_excel(file_path, sheet_name)
        else:
            self.df.to_excel(file_path, sheet_name)

    def plot_results(self, x="t"):
        if x == "t" and not self.data_is_vals:
            x = None
        if isinstance(x, str):
            x += f" ({UNITS_OF_ATTR.get(x, '')})"

        df = self.df
        if df.empty:
            return
        else:
            df.loc[:, df.columns != "car_id"].plot_results(x=x)


class Road:
    def __init__(self, start, end, width, color, v_max, with_arrows, priority, car_factory, sign, sensors, obj_id):
        """
        Route droite.

        :param start: coordonnées du début
        :param end: coordonnées de la fin
        :param width: largeur
        :param color: couleur
        :param v_max: limite de vitesse de la route
        :param with_arrows: si des flèches seront affichées sur la route ou non
        :param priority: priorité des voitures de la route
        :param car_factory: éventuelle CarFactory
        :param sign: éventuel élément de signalisation : feu de signalisation ou panneau stop
        :param sensors: éventuels capteurs
        :param obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.simulation = get_by_id(0)
        self.start, self.end = npa((start, end))
        self.width = width
        self.color = color
        self.with_arrows = with_arrows
        self.priority = priority

        self.length = distance(self.start, self.end)  # longueur de la route
        self.vd = direction_vector(self.start, self.end)  # vecteur directeur de la route, normé
        vn = normal_vector(self.vd, self.width / 2)  # vecteur normal pour les coord des sommets
        self.vertices = self.start + vn, self.start - vn, self.end - vn, self.end + vn  # coordonnées des sommets, pour l'affichage
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
        rarete = sc.road_arrow_period  # inverse de la fréquence des flèches
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
            sensor.d = self.length * sensor.d_ratio

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

            # mise à jour de d, v et a
            car.update(dt)
            car.soon_colliding_cars = []

            # transition douce du v_max avec celui de la prochaine route
            car.v_max = self.v_max_transition(car)

            # mise à jour de la position et des sommets d'affichage
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

        car.next_road = self.car_sorter.sorter(self.simulation.t)  # récupération de la prochaine route de la voiture

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

        elif car.next_road is not None and car.d >= self.length * (1 - sc.road_transition_size):
            alpha = (car.d - self.length * (1 - sc.road_transition_size)) / (self.length * sc.road_transition_size)
            v_max1 = self.v_max
            v_max2 = car.next_road.v_max
            return alpha * v_max2 + (1 - alpha) * v_max1

        else:
            return car.v_max


class SRoad(Road):
    def __init__(self, start, end, width, color, v_max, priority, obj_id):
        """Sous-route droite composant ArcRoad, dérivant de Road."""
        super().__init__(start, end, width, color, v_max, False, priority, None, None, None, obj_id)

    def __repr__(self):
        return "S" + super().__repr__()


class ArcRoad:
    def __init__(self, start, end, vdstart, vdend, v_max, n, width, color, priority, car_factory, obj_id):
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
        self.v_max = v_max * sc.arcroad_slow_coeff

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
            sroad = SRoad(rstart, rend, width, color, self.v_max, priority, None)
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
