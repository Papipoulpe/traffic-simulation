import pandas as pd

from .math_and_util import *


class Car:
    def __init__(self, v: float = sc.car_v, a: float = sc.car_a, length: float = sc.car_length,
                 width: float = sc.car_width, a_max: float = sc.a_max, a_min: float = sc.a_min,
                 t_react: float = sc.t_react, color: Color = sc.car_color, obj_id: int | None = None, **kwargs):
        """
        Objet voiture, ou plus largement tout véhicule de la simulation. Une voiture est toujours
        rattachée à une route. Sa position est déterminée par la route auquelle elle est rattachée et la distance qu'
        elle a parcourue depuis la début de cette route. Cette distance, ainsi que sa vitesse et son accélération, sont
        éventuellement mis à jour à chaque image de la simulation.

        Ainsi, pour une voiture, une itération de la simulation se déroule généralement de la manière suivante :        \n
        - la simulation détermine les autres voitures ayant un risque de collision avec la voiture
        - la route de la voiture lui fournit son leader
        - la voiture calcule son leader vituel équivalent puis met à jour son accélération, sa vitesse et sa distance
          depuis le début de la route
        - la route met à jour la position (x, y) de la voiture, ce qui actualise tous les attributs qui en dépendent
          (rectangle d'affichage, zones de collision...)

        Args:
            v: vitesse initiale, en m/s
            a: accélération initiale, en m/s²
            length: longueur, en m
            width: largeur, en m
            a_max: accélération maximale, en m/s²
            a_min: décélération minimale, en m/s² (négative, a priori)
            t_react: temps de réaction du conducteur, en s
            color: couleur
            obj_id: éventuel identifiant
        """
        # attributs constants
        self.id = new_id(self, obj_id, pos=kwargs.get("pos_id", True))
        self.color = color
        self.length = length * sc.scale
        self.width = width * sc.scale

        # route et prochaine route de la voiture
        self.road = ...  # définie dans road.new_car()
        self.next_road = None  # définie par le CarSorter de self.road

        # coordonnées, vitesse et accélération
        self.d = 0  # distance du centre du véhicule jusqu'au début de la route
        self._pos = npz(2)  # position du centre du véhicule
        self.v = v * sc.scale if v is not None else None  # vitesse instantanée, sera remplacée par self.road.v_max si None
        self.a = a * sc.scale  # accélération instantanée

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

        self.leaders = []  # leaders de la voiture : liste de couples (d, v) où d est la distance par la route à une autre voiture et v sa vitesse
        self.soon_colliding_cars = []  # voitures en potentielle collision avec la voiture : liste de Car

        # historique de certains attributs et sauvegarde de données pour les capteurs
        self.date_of_birth = -1  # seconde où la voiture est créée
        self.d_traveled = 0  # distance totale parcourue
        self.attr_history = {"d(t)": {}, "v(t)": {}, "a(t)": {}}  # attributs en fonction du temps

    def __repr__(self):
        return f"Car(id={self.id}, pos={self.pos}, d={self.d}, v={self.v}, a={self.a}, v_max={self.v_max}, " \
               f"virtual_leader={self.virtual_leader}, soon_colliding_cars={self.soon_colliding_cars}, " \
               f"leaders={self.leaders}, next_road={self.next_road}, color={closest_color(self.color)})"

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        """car.pos.setter : quand car.pos est mis à jour, cette fonction est exécutée est met à jour les autres
        attributs de la voiture qui en dépendent (sommets pour l'affichage, les sommets des zones de collision) par la
        même occasion."""
        self._pos = pos

        vd = self.road.vd  # on récupère le vecteur directeur de la route
        vd_l = vd * self.length / 2  # on le norme pour la longueur de la voiture
        vn_w = normal_vector(
            self.road.vd,
            self.width / 2)  # vecteur normal de la route normé pour la largeur de la voiture
        vn_ddm = normal_vector(
            self.road.vd,
            self.delta_d_min / 2)  # vn de la route normé pour la longueur de la zone de collision de devant

        # sommets d'affichage
        c1 = self.pos + vn_w - vd_l  # derrière droit
        c2 = self.pos - vn_w - vd_l  # derrière gauche
        c3 = self.pos - vn_w + vd_l  # devant gauche
        c4 = self.pos + vn_w + vd_l  # devant droit
        self.vertices = c1, c2, c3, c4

        # sommets de la zone de collision devant
        vd_ddmp = vd * (self.delta_d_min + self.v * self.t_react)  # vecteur directeur de la route normé pour la distance de sécurité et la vitesse de la voiture
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
        Actualise les coordonnées du mouvement (position, vitesse, accélération) de la voiture :
        - calcul le leader vituel équivalent de la voiture
        - en déduit son accélération, puis sa vitesse et sa position sur la route
        - met à jour sa position sur la fenêtre et ses attributs qui en dépendent

        Args:
            dt: durée du mouvement
        """
        prev_d = self.d

        if sc.use_idm:
            a_iidm = iidm(self, self.virtual_leader)  # si l'IDM est utilisé, on met à jour l'accélération
            self.a = max(a_iidm, self.a_min)  # on la minore par a_min

        update_taylor(self, dt)  # mise à jour de d et v par développement de Taylor (en place)

        self.pos = self.road.dist_to_pos(self.d)  # mise à jour de la position et ce qui en dépend

        # sauvergarde des attributs
        t = round(self.road.simulation.t, 2)
        delta_d = self.d - prev_d
        self.d_traveled += delta_d

        atm_sensors = sc.dynamic_data["atm_sensors"]

        if atm_sensors.get("d(t)"):
            self.attr_history["d(t)"][t] = scale_to_si_unit("d(t)", self.d_traveled)
        if atm_sensors.get("v(t)"):
            self.attr_history["v(t)"][t] = scale_to_si_unit("v(t)", self.v)
        if atm_sensors.get("a(t)"):
            self.attr_history["a(t)"][t] = scale_to_si_unit("a(t)", self.a)

    @property
    def virtual_leader(self):
        """Renvoie la distance au et la vitesse d'un leader virtuel équivalent de la voiture, i.e. un couple (d, v) où :

        - si la voiture est en prévision de collision avec d'autres voitures, c'est-à-dire si ``car.bumping_cars``
        n'est pas vide, alors d est la moyenne des distances à vol d'oiseau entre la voiture et les voitures de
        ``car.bumping_cars`` et v est la moyenne de leurs vitesses projetées selon le vecteur directeur de sa route

        - sinon, d est la moyenne des distances par la route jusqu'aux voitures représentées dans ``car.leaders`` et v
        la moyenne de leurs vitesses."""
        # si la voiture va peut être rentrer dans d'autres voitures, seules celles-ci seront prises en compte
        if self.soon_colliding_cars:
            # on fait la moyenne des distances à vol d'oiseau et la moyenne des vitesses pondérées par le produit
            # scalaire des vecteurs directeurs des routes
            virtual_leader_coords = npz(2)

            for other_car in self.soon_colliding_cars:
                d = max(distance(self.pos, other_car.pos) - self.length / 2 - other_car.length / 2, 0)
                v = other_car.v * (self.road.vd @ other_car.road.vd)
                virtual_leader_coords += npa([d, v])

            return virtual_leader_coords / len(self.soon_colliding_cars)

        # sinon, si la simulation/route fournit des leaders, on prend la moyenne de leurs distances/vitesses
        elif self.leaders:
            virtual_leader_coords = npz(2)
            total_p = 0

            for leader, d, p in self.leaders:
                virtual_leader_coords += npa([d, leader.v]) * p
                total_p += p

            return virtual_leader_coords / total_p

        # sinon, on renvoie None
        else:
            return None

    def may_collide_with(self, other_car: "Car"):
        """Renvoie si la voiture va **percuter** ``other_car``, c'est-à-dire si ``car.front_bumper_hitbox``  et
        ``other_car.side_bumper_hurtbox`` s'intersectent."""
        return do_polygons_intersect(self.front_bumper_hitbox, other_car.side_bumper_hurtbox)

    def might_collide_with(self, other_car: "Car"):
        """Renvoie si la voiture et ``other_car`` vont se rentrer dedans, c'est-à-dire si ``car.front_bumper_hitbox``
        et ``other_car.front_bumper_hitbox`` s'intersectent. Équivalent à ``other_car.might_collide_with(car)``."""
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


class CarFactory:
    def __init__(self, freq=None, crea=None, obj_id=None):
        """
        Objet CarFactory, qui gère la création de voitures à l'entrée d'une route. Une CarFactory est
        associée à une et une seule route. Au début de la simulation, elle génère selon les paramètres de l'utilisateur
        deux fonctions : une fonction de fréquence de création, qui sera appellée à chaque itération de la simulation
        et renvoie un booléen indicant si une voiture doit être créée ou non, et une fonction de création, qui sera
        appellée si la fonction de fréquence de création renvoie une réponse positive et renvoie un objet Car étant la
        nouvelle voiture crée.

        Ainsi, pour un CarFactory, une itération de la simulation se déroule généralement de la manière suivante :      \n
        - la simulation exécute la fonction de fréquence de création en lui fournissant les arguments requis
          (typiquement, le temps)
        - si elle renvoie True, la fonction de création est exécutée et renvoie une nouvelle voiture

        Args:
            freq: fréquence de création de voiture, peut être de type ``[a, b]`` pour une pause aléatoire d'une durée
                entre a et b secondes entre la création de deux voiture, ``a`` pour une fréquence constante, une fonction
                ``f(t: float) -> bool`` ou vide pour aucune création
            crea: manière de choisir la voiture à créer, peut être de type ``{"arg": val, ...}``, ``"rand_color"``,
                ``"rand_length"`` et/ou ``"rand_width"``, une fonction ``f(t: float) -> Car`` ou vide pour la voiture
                par défaut
            obj_id: éventuel identifiant
        """
        # attributs constants
        self.id = new_id(self, obj_id)
        self.road = ...
        self.args = [freq, crea]

        # éventuellement utilisé pour fréquence aléatoire, prochain instant où une voiture doit être créée
        self.next_t = ...

        # initialisation des fonctions
        self.freq_func = self.init_freqfunc(freq)
        self.crea_func = self.init_creafunc(crea)

    def __repr__(self):
        return f"CarFactory(id={self.id}, freq_arg={self.args[0]}, crea_arg={self.args[1]})"

    def init_freqfunc(self, arg):
        """Génère une fonction de fréquence de création, en fonction de ce qu'a fourni l'utilisateur (voir doc de
        self.__init__)."""
        if isinstance(arg, (int, float)) or (isinstance(arg, (tuple, list)) and arg[0] == arg[1]):
            # si de type a ou [a, a], renvoie True toutes les a secondes
            if isinstance(arg, (list, tuple)):
                # si de type [a, a], on récupère le a
                a = arg[0]
            else:
                a = arg

            def freq_func(t):
                right_time = round(t, 2) % a == 0  # True toute les a secondes
                # on vérifie qu'il y a de la place sur la route, sauf si sc.car_fact_force_crea est True
                if right_time and not sc.car_fact_force_crea and self.road.cars:
                    last_car = self.road.cars[-1]
                    enough_space_available = last_car.d - last_car.length / 2 > sc.car_fact_rand_length_max + sc.delta_d_min
                    return enough_space_available
                else:
                    return right_time

            return freq_func

        elif isinstance(arg, (tuple, list)):
            # si de type [a, b], attendre aléatoirement entre a et b secondes : self.next_t est le prochain instant ou
            # la création sera permise, et on lui rajoutera un delai aléatoire entre a et b à chaque fois qu'il sera
            # dépassé
            a, b = arg
            self.next_t = np.random.uniform(a, b)

            def freq_func(t):
                if t >= self.next_t:
                    delay = np.random.uniform(a, b)
                    self.next_t += delay
                    # on vérifie qu'il y a de la place sur la route, sauf si sc.car_fact_force_crea est True
                    if not sc.car_fact_force_crea and self.road.cars:
                        last_car = self.road.cars[-1]
                        space_available = last_car.d - last_car.length / 2 > sc.car_fact_rand_length_max + sc.delta_d_min
                        return space_available
                    else:
                        return True
                else:
                    return False

            return freq_func

        elif arg is None:  # si aucune création
            return None

        else:  # si une fonction du temps est fournie
            def freq_func(t):
                right_time = arg(t)
                # on vérifie qu'il y a de la place sur la route, sauf si sc.car_fact_force_crea est True
                if self.road.cars and not sc.car_fact_force_crea:
                    last_car = self.road.cars[-1]
                    space_available = last_car.d - last_car.length / 2 > sc.car_fact_rand_length_max + sc.delta_d_min
                    return right_time and space_available
                else:
                    return right_time

            return freq_func

    def init_creafunc(self, arg):
        """Génère une fonction de création, en fonction de ce qu'a fourni l'utilisateur (voir doc de self.__init__)."""
        if not isinstance(arg, (str, list, dict, type(None))):
            # si arg est une fonction, on l'utilise
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
                attrs["color"] = [np.random.randint(sc.car_fact_rand_color_min, sc.car_fact_rand_color_max) for _ in
                                  range(3)]

            if "rand_length" in args:
                attrs["length"] = np.random.uniform(sc.car_fact_rand_length_min, sc.car_fact_rand_length_max)

            if "rand_width" in args:
                attrs["width"] = np.random.uniform(sc.car_fact_rand_width_min, sc.car_fact_rand_width_max)

            for a in args:
                if isinstance(a, dict):
                    for key in a:
                        attrs[key] = a[key]

            if attrs.get("v") is None:
                attrs["v"] = self.road.v_max / sc.scale  # /sc.scale car Car prend des arguments en unités SI

            return Car(**attrs)

        return crea_func

    def factory(self, args_fact: dict, args_crea: dict):
        """
        Renvoie une voiture générée par la fonction de création si la fonction de fréquence de création l'autorise.

        Args:
            args_fact: dictionnaire d'arguments pour la fonction de
                fréquence de création
            args_crea: dictionnaire d'arguments pour la fonction de
                création
        """
        # si une fonction de fréquence de création est définie et qu'elle autorise la création
        if self.freq_func is not None and self.freq_func(**args_fact):
            # on renvoie la voiture créée par la fonction de création
            return self.crea_func(**args_crea)


class CarSorter:
    def __init__(self, method=None, obj_id=None):
        """
        Objet CarSorter, gèrant les prochaines routes des voitures quittant la route. Au démarrage de la
        simulation, chaque route se voit assigné un CarSorter, dont elle appellera la fonction de tri dès qu'une
        voiture la rejoint pour définir sa prochaine route.

        Ainsi, pour un CarSorter, une itération de la simulation se déroule généralement de la manière suivante :       \n
        - la route associée reçoit éventuellement une nouvelle voiture
        - elle appelle la fonction de tri de son CarSorter et assigne le résultat à l'attribut next_road de la voiture

        Args:
            method: id de route, dictionnaire id -> proba, fonction f(t) -> id ou None (voir la doc de
                simulation.set_road_graph)
        """
        # attributs constants
        self.id = new_id(self, obj_id)
        self.method = method  # méthode de tri

        # initialisation de la fonction de tri
        self.sorter = self.init_sorter(method)

    def __repr__(self):
        return f"CarSorter(id={self.id}, method={self.method})"

    def init_sorter(self, arg):
        """Génère une fonction de tri selon l'argument fourni."""
        if not arg:
            # si l'argument est None, renvoie une fonction renvoyant toujours None
            self.method = None
            return empty_function

        elif isinstance(arg, int):
            # si l'argument est un id de route, renvoie une fonction renvoyant toujours la route associée
            return lambda *_, **__: get_by_id(arg)

        elif isinstance(arg, dict):
            # si l'argument est un disctionnaire associant un id de route à une proba, renvoie une fonction prenant une
            # des routes aléatoirement
            probs, roads = [], []
            for road in arg:
                probs.append(arg[road])
                roads.append(road)

            def sort_func(*_, **__):
                return get_by_id(np.random.choice(roads, p=probs))

            return sort_func

        else:
            # si l'argument est une fonction fournie par l'utilisateur, on l'utilise
            self.method = "user func"
            return lambda t: get_by_id(arg(t))


class TrafficLight:
    def __init__(self, state_init: int, static=False, obj_id: int = None):
        """
        Objet du feu tricolore de signalisation. Au démarrage de la simulation, chaque route se voit
        assigné un élément de signalisation : soit l'utilisateur en fournit un pour la route, soit la simulation
        donne un feu constamment vert. A un état du feu (vert, orange, rouge) est associé une fausse voiture, qui sera
        donnée comme leader à la première voiture de la route, ce qui imite la réaction d'un conducteur face au feu.

        Ainsi, pour un feu, une itération de la simulation se déroule généralement de la manière suivante :             \n
        - la simulation met à jour l'état du feu, ce actualise la fausse voiture du feu
        - la route récupère cette voiture et la fournit à sa première voiture

        Args:
            state_init: état initial du feu : 0 = rouge, 1 = orange, 2 =
                vert
            static: si l'état du feu reste invariant pendant la simulation
            obj_id: éventuel identifiant
        """
        # attributs constants
        self.id = new_id(self, obj_id)
        self.static = static  # si le feu change d'état durant la simulation
        self.width = sc.tl_width  # épaisseur du trait représentant le feu
        self._road: Road = ...  # route auquelle le feu est rattaché
        self.pos = npz(2)  # position, définie dans road.setter
        self.vertices = npz((4, 2))  # sommets pour affichage, définis dans road.setter
        self.dummy_cars = {}  # fausses voitures du feu, définies dans road.setter

        # état du feu
        self.state = self.state_init = state_init  # signalisation du feu : rouge 0, orange 1 ou vert 2

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

        self.pos = road.dist_to_pos(road.length - self.width / 2)  # position du feu

        vd = self.road.vd * sc.tl_width / 2
        vn = normal_vector(vd, self.road.width / 2)
        self.vertices = self.pos - vd + vn, self.pos - vd - vn, self.pos + vd - vn, self.pos + vd + vn  # sommets pour l'affichage

        dummy_car_red = Car(v=0, length=0, pos_id=False)  # fausse voiture pour le feu rouge
        dummy_car_red.d = self.road.length
        dummy_car_orange = Car(v=0, length=0, pos_id=False)  # fausse voiture pour le feu orange
        dummy_car_orange.d = self.road.length + sc.delta_d_min / sc.tl_orange_deceleration_coeff
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
        Objet panneau de signalisation stop. Au démarrage de la simulation, chaque route se voit
        assigné un élément de signalisation : soit l'utilisateur en fournit un pour la route, soit la simulation
        donne un feu constamment vert. Chaque panneau stop a une fausse voiture, qui sera donnée comme leader à la
        première voiture de la route, ce qui imite la réaction d'un conducteur face au panneau stop.

        Ainsi, pour un panneau stop, une itération de la simulation se déroule généralement de la manière suivante :    \n
        - la route récupère la fausse voiture du panneau stop et la fournit à sa première voiture

        Args:
            obj_id: éventuel identifiant
        """
        # attributs constants
        self.id = new_id(self, obj_id)
        self.pos = npz(2)  # position dans sur la fenêtre
        self.vertices = npz((4, 2))  # sommets pour l'affichage
        self._road = ...  # route du panneau, définie dans road.init_sign
        self.dummy_car = ...  # fausse voiture, définie dans self.road.setter

    def __repr__(self):
        return f"StopSign(id={self.id})"

    @property
    def road(self):
        return self._road

    @road.setter
    def road(self, road):
        """stop_sign.road.setter : quand stop_sign.road est mis à jour, cette fonction est exécutée et met à jour la
        postion, les sommets d'affichage et la fausse voiture du panneau stop par la même occasion.
        """
        self._road = road
        self.pos = road.dist_to_pos(road.length)

        vd = self.road.vd * sc.ss_width / 2
        vn = normal_vector(vd, self.road.width / 2)
        self.vertices = self.pos - vd, self.pos - vn, self.pos + vd, self.pos + vn

        dummy_car = Car(v=0, length=0, pos_id=False)
        dummy_car.d = road.length + sc.delta_d_min + 10 / sc.ss_deceleration_coeff
        dummy_car._pos = self.pos
        self.dummy_car = dummy_car


class Sensor:
    def __init__(self, position: float = 1, attributes_to_monitor: str | Sequence[str] | None = ("v", "a"),
                 obj_id=None):
        """
        Objet capteur. Un capteur est associé à une route et récupère des données de la simulation, plus précisement
        des attributs des voitures qui dépasse la position du capteur au sein de la route. Ces attributs sont définis
        par l'utilisateur lors de la création du capteur. A la fin de la simulation, l'utilisateur peut récupérer ces
        données, sous forme de graphes ou en les exportant dans des fichiers de différents types. Une route peut avoir
        plusieurs capteurs.

        Ainsi, pour un capteur, une itération se déroule généralement de la manière suivante :
        - il regarde chaque voiture de la route
        - pour celles qu'il n'a jamais vu et qui l'ont dépassé, il enregistre certains de leurs attributs et note la
        date

        Args:
            position: proportion de la route où sera placé le capteur (0
                = au tout début, 0.5 = au milieu, 1 = à la toute fin)
            attributes_to_monitor: les attributs des voitures à
                surveiller, en chaînes de caractères : None pour juste
                compter le nombre de voitures, ou autant que voulu parmi
                ``v``, ``a``, ``length``, ``width``, ``color``, ``age``, ``date_of_birth`` et
                ``d_travelled`` ou parmi ``d(t)``, ``v(t)`` et ``a(t)``
        """
        # attributs constants
        self.id = new_id(self, obj_id)
        self.d_ratio = position  # position en fraction de la longueur de la route
        self.d = 0  # distance entre le capteur et le début de la route, définie dans self.road.setter
        self.vertices = npz((4, 2))  # sommets d'affichage, définis dans self.road.setter
        self._road = ...  # route à laquelle le capteur est rattaché, définie dans road.init_sensor
        self.inst_data = True  # si le capteur récupère les valeurs instantanées des attributs des voitures ou l'historique de ces valeurs
        self.attributes_to_monitor = self.init_atm(attributes_to_monitor)  # attributs surveillés des voitures

        # stockage des données
        self.already_seen_cars_id = {}  # id des voitures déjà vues
        self.data = []  # données brutes, de la forme [t, car_id, attr1, ...]
        self.df = None  # données sous forme de DataFrame, calculées dans self.compute_results()

    def __repr__(self):
        return f"Sensor(id={self.id}, position={self.d_ratio}, attributes_to_monitor={self.attributes_to_monitor}, road_id={self.road.id})"

    def init_atm(self, atm):
        if atm is None:
            return []

        elif isinstance(atm, str):
            atm = [atm]

        if any(attr in ["d(t)", "v(t)", "a(t)"] for attr in atm):
            self.inst_data = False
            for attr in atm:
                sc.dynamic_data["atm_sensors"][attr] = True
        else:
            self.inst_data = True

        return list(atm)

    @property
    def road(self):
        return self._road

    @road.setter
    def road(self, road):
        self._road = road
        self.d = road.length * self.d_ratio
        vn_w = normal_vector(self.road.vd, self.road.width / 2)
        vd = self.road.vd
        vd_l = vd * sc.sensor_width / 2
        pos = self.road.dist_to_pos(self.d)
        c1 = pos + vn_w - vd_l
        c2 = pos - vn_w - vd_l
        c3 = pos - vn_w + vd_l
        c4 = pos + vn_w + vd_l
        self.vertices = c1, c2, c3, c4

    def compute_results(self, since, how_many):
        """Création du DataFrame à partir des données brutes du capteur.

        Args:
            since: date minimum pour les données
            how_many: nombre de dernières voitures à garder
        """
        # liste des attributs avec leurs unités
        atm_with_units = [f"{attr} ({UNITS_OF_ATTR.get(attr, '')})" for attr in self.attributes_to_monitor]

        if self.inst_data:
            # pour des données instantanées, on crée un simple DataFrame en retirant les données trop veilles
            data = self.data.copy()  # copie des données pour traitement

            if how_many < INF:
                # on retire des données des premières voitures
                data = data[-how_many::]

            if since > 0:
                # on retire les données trop vieilles
                processed_data = []
                for data_row in data:
                    if data_row[0] >= since:
                        processed_data.append(data_row)
                data = processed_data

            # création du DataFrame
            self.df = pd.DataFrame(data=data, columns=["t (s)", "car_id"] + atm_with_units)

        else:
            # pour des fonctions du temps, on utilise un MultiIndex avec un produit des noms des fonctions et des id des
            # voitures
            index = set()  # index du DataFrame, union des ensembles de définition des fonctions du temps
            cars_id = []  # id des voitures dont les données n'ont pas été retirées pendant le traitement
            data = self.data.copy()  # copie des données pour traitement

            if how_many < INF:
                # on retire les données des premières voitures
                data = data[-how_many::]

            for data_t, car_id, time_to_vals_dic, *_ in data:
                # on construit l'index en gardant les dates nécessaires
                if data_t >= since:
                    index = index.union(set(time_to_vals_dic.keys()))
                    cars_id.append(car_id)

            index = sorted(index)  # tri des dates et conversion en liste
            processed_data = []

            for t in index:
                # on retire les données trop vieilles en utilisant les dates de l'index
                row = []
                for _, car_id, *time_to_val_dics in data:
                    if car_id in cars_id:
                        for time_to_val_dic in time_to_val_dics:
                            val = time_to_val_dic.get(round(t, 4))
                            row.append(val)

                processed_data.append(row)

            # création du MultiIndex
            multi_index = pd.MultiIndex.from_product([cars_id, atm_with_units], names=["car_id", "f(t)"])

            # création du DataFrame
            self.df = pd.DataFrame(data=processed_data, columns=multi_index, index=index)

    def watch_car(self, car, t):
        """Récupère les attributs à surveiller d'une voiture."""
        data_row = [t, car.id]

        for attr in self.attributes_to_monitor:
            if attr == "age":
                val = t - car.date_of_birth
            elif self.inst_data:
                val = car.__getattribute__(attr)
            else:
                val = car.attr_history[attr]

            val = scale_to_si_unit(attr, val)
            data_row.append(val)

        self.data.append(data_row)
        self.already_seen_cars_id[car.id] = 1

    def watch_road(self, t):
        """Récupère les attributs à surveiller des voitures d'une route ayant dépassé le capteur."""
        for car in self.road.cars:
            if car.id not in self.already_seen_cars_id and car.d >= self.d:
                self.watch_car(car, t)

    def results(self, form: str = "str", describe: bool = True, **kwargs):
        """Met en forme les données du capteur. Les données doivent être préalablement traitées avec compute_results()."""
        df = self.df

        if describe:
            df = pd.concat([df, df.describe()])

        if form == "str":
            return str(df)

        else:
            return getattr(df, f"to_{form}")(**kwargs)

    def export_results(self, file_path: str, sheet_name: str, describe: bool = True):
        """Exporte les données du capteur vers un fichier Excel. Les données doivent être préalablement traitées avec
        compute_results()."""
        df = self.df

        if describe:
            pd.concat([df, df.describe()]).to_excel(file_path, sheet_name)
        else:
            df.to_excel(file_path, sheet_name)

    def plot_results(self, **plot_kwargs):
        """Graphe les données du capteur. Les données doivent être préalablement traitées avec compute_results()."""
        if "x" not in plot_kwargs:
            plot_kwargs["x"] = "t"

        if plot_kwargs["x"] == "t" and not self.inst_data:
            plot_kwargs["x"] = None

        if isinstance(plot_kwargs["x"], str):
            plot_kwargs["x"] += f" ({UNITS_OF_ATTR.get(plot_kwargs['x'], '')})"

        if "title" not in plot_kwargs:
            plot_kwargs["title"] = str(self)

        df = self.df

        if df.empty:
            return

        else:
            df.loc[:, df.columns != "car_id"].plot(**plot_kwargs)


class Road:
    def __init__(self, start, end, color, v_max, with_arrows, priority, heavily_traveled, car_factory, sign, sensors, obj_id):
        """
        Objet route droite. Une route droite gère des voitures, un élement de signalisation et des capteurs, et est
        utilise un CarFactory qui gère la création de ses voitures et un CarSorter qui gère le tri des voitures qui
        sortent de la route. Une route va d'un point à un autre, a une limite de vitesse et un indice de priorité (si
        son indice de priorité est plus grand que celui d'une autre route, ses voitures seront prioritaires devant
        celles de l'autre route). Ses prédécesseures et successeures sont définies dans le graphe des routes, que
        l'utilisateur définie au début de la simulation.

        Ainsi, pour une route droite, une itération de la simulation de déroule généralement de la manière suivante :
        - la simulation détermine les leaders de la première voiture de la route (qu'on appelera "leaders de la route")
        en cherchant les prochaines voitures parmi les autres routes
        - la route actualise ses voitures une par une, en donnant comme leaders à la première voiture soit la fausse
        voioture de son élément de signalisation si elle existe, soit les leaders de la route, et au autres voitures la
        voiture qu'elle ont devant elle
        - si une voiture a dépassé une certaine distance, la route met à jour son v_max pour le faire varier doucement
        vers celui de sa prochaine route
        - si une voiture a dépassé la longueur de la route, on soustrait à sa distance parcourue la longueur de la
        route et, si elle existe, on l'ajoute à sa prochaine route
        - la simulation met à jour son élément de signalisation et ses capteurs, et utilise son CarFactory pour créer
        une voiture si besoin, qui se voit assigner une prochaine route en utilisant le CarSorter

        Args:
            start: coordonnées du début
            end: coordonnées de la fin
            color: couleur
            v_max: limite de vitesse de la route
            with_arrows: si des flèches seront affichées sur la route ou
                non
            priority: priorité des voitures de la route
            heavily_traveled: si la route est dans une zone de trafic dense, où les collisions doivent être détectées
            car_factory: éventuelle CarFactory
            sign: éventuel élément de signalisation : feu de
                signalisation ou panneau stop
            sensors: éventuels capteurs
            obj_id: éventuel identifiant
        """
        # attributs constants
        self.id = new_id(self, obj_id)
        self.simulation = get_by_id(0)
        self.start, self.end = start, end
        self.width = sc.road_width * sc.scale
        self.color = color
        self.with_arrows = with_arrows  # si la simulation affiche des flèches pour la route ou non
        self.priority = priority  # indice de priorité de la route
        self.is_heavily_traveled = heavily_traveled  # si dans une zone de trafic dense ou non
        self.v_max = v_max  # vitesse limite de la route

        self.length = distance(self.start, self.end)  # longueur de la route
        self.vd = direction_vector(self.start, self.end)  # vecteur directeur de la route, normé
        vn = normal_vector(self.vd, self.width / 2)  # vecteur normal pour les coord des sommets
        self.vertices = self.start + vn, self.start - vn, self.end - vn, self.end + vn  # coordonnées des sommets, pour l'affichage
        self.angle = angle_of_vect(self.vd)  # angle de la route par rapport à l'axe des abscisses

        self.car_sorter = CarSorter()
        self.car_factory = self.init_car_factory(car_factory)
        self.sign = self.init_sign(sign)
        self.sensors = self.init_sensors(sensors)

        # liste des voitures appartenant à la route
        self.cars: list[Car] = []

    def __repr__(self):
        return f"Road(id={self.id}, start={self.start}, end={self.end}, length={self.length}, vd={self.vd}, color={closest_color(self.color)})"

    def init_car_factory(self, car_factory):
        """Initialise la CarFactory de la route."""
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
        """Initialise le/les capteur/s de la route."""
        if isinstance(sensors, Sensor):
            sensors.road = self
            return [sensors]

        elif sensors is None:
            return []

        else:
            for sensor in sensors:
                sensor.road = self  # sensor.road.setter gère tout
            return sensors

    def dist_to_pos(self, d):
        """Renvoie les coordonnées d'un objet de la route à une distance ``d`` du début de la route."""
        return self.start + self.vd * d

    def update_cars(self, dt, leaders):
        """Bouge les voitures de la route à leurs positions après dt.

        Args:
            dt: durée du mouvement
            leaders: voitures leaders de la première voiture de la route
        """
        sign_car = self.sign.dummy_car  # on récupère la fausse voiture du feu/stop de la route

        for i, car in enumerate(self.cars):
            if i > 0:
                # pour toutes les voitures sauf la première, donner la voiture suivante
                leading_car = self.cars[i - 1]
                car.leaders = [(leading_car, (leading_car.d - leading_car.length / 2) - (car.d + car.length / 2), 1)]

            elif sign_car is not None:
                # si l'élement de signalisation est actif et que le leader le plus proche est assez loin, on utilise sa
                # fausse voiture pour la première voiture
                sign_car_d = sign_car.d - (car.d + car.length / 2)

                if leaders:
                    closest_road_leader_tuple = min(leaders, key=lambda leader: leader[1])
                    closest_road_leader_d = closest_road_leader_tuple[1] + (self.length - car.d - car.length / 2) - closest_road_leader_tuple[0].length / 2

                    if sign_car_d >= closest_road_leader_d:
                        car.leaders = [(leader, closest_road_leader_d, p) for leader, d, p in
                                       leaders]
                    else:
                        car.leaders = [(sign_car, sign_car_d, 1)]
                else:
                    car.leaders = [(sign_car, sign_car_d, 1)]

            else:
                # sinon pour la première voiture, donner les leaders de la route en ajustant les distances
                car.leaders = [(leader, d + self.length - (car.d + car.length / 2), p) for leader, d, p in leaders]

            # mise à jour des vecteurs du mouvmement de la voiture
            car.update(dt)
            car.soon_colliding_cars = []

            # transition douce du v_max avec celui de la prochaine route
            car.v_max = self.v_max_transition(car)

            if car.d > self.length:  # si la voiture sort de la route
                car.d -= self.length  # on initialise le prochain d
                if car.next_road is not None:
                    car.next_road.new_car(car)  # on l'ajoute à la prochaine route si elle existe
                self.cars.remove(car)  # on retire la voiture de la liste des voitures (pas d'impact sur la boucle avec enumerate)

    def update_sensors(self, t):
        """Met à jour les capteurs de la route."""
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

        if car.date_of_birth == -1:
            car.date_of_birth = self.simulation.t

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
        """Fonction pour faire une transition douce entre deux routes qui n'ont pas la même limite de vitesse."""
        d_min_for_transition = self.length * (1 - sc.road_transition_size)  # d minimum pour faire la tansition

        if isinstance(self, SRoad) or (car.next_road is None) or (car.d <= d_min_for_transition):
            # si la route est une SRoad, que la voiture n'a pas de prochaine route ou qu'elle est trop loin
            return car.v_max

        else:
            alpha = (car.d - d_min_for_transition) / (self.length * sc.road_transition_size)
            v_max1 = self.v_max
            v_max2 = car.next_road.v_max
            return alpha * v_max2 + (1 - alpha) * v_max1


class SRoad(Road):
    def __init__(self, start, end, color, v_max, priority, heavily_traveled, obj_id):
        """Route droite composant une ArcRoad, dérivant de Road. Elle n'a ni flèches, ni élément de signalisation, ni
        capteurs, ni CarFactory."""
        super().__init__(start, end, color, v_max, False, priority, heavily_traveled, None, None, None, obj_id)

    def __repr__(self):
        return "S" + super().__repr__()


class ArcRoad:
    def __init__(self, start, end, vdstart, vdend, v_max, with_arrows, heavily_traveled, n, color, priority, obj_id):
        """
        Objet route courbée, composée de multiples routes droites SRoad. N'est pas une route en soit mais un objet qui
        gère la création d'un ensemble de routes, puis qui n'est plus utilisé de la simulation.

        Args:
            start: coordonnées du début
            end: coordonnées de la fin
            vdstart: vecteur directeur de la droite asymptote au début
            vdend: vecteur directeur de la droite asymptote à la fin
            n: nombre de routes droites formant la route courbée
            color: couleur
            obj_id: éventuel identifiant
        """
        self.id = new_id(self, obj_id)
        self.start, self.end = start, end
        self.with_arrows = with_arrows
        self.v_max = v_max * sc.arcroad_deceleration_coeff
        self.n = n

        intersec = lines_intersection(start, vdstart, end, vdend)
        self.points = bezier_curve(self.start, intersec, self.end, n + 1)  # n + 1 points pour n routes
        self.length = sum(distance(self.points[i], self.points[i + 1]) for i in range(n))
        self.sroads = self.init_sroads(self.v_max, n, color, priority, heavily_traveled)

        self.car_factory = CarFactory()
        self.sign, self.update_sign = None, empty_function
        self.sensors, self.update_sensors = [], empty_function

    def init_sroads(self, v_max, n, color, priority, heavily_traveled):
        sroads = []
        for i in range(n):
            rstart = self.points[i]
            rend = self.points[i + 1]
            sroad = SRoad(rstart, rend, color, v_max, priority, heavily_traveled, None)
            sroads.append(sroad)

        return sroads

    def __repr__(self):
        return f"ArcRoad(id={self.id}, start={self.start}, end={self.end}, length={self.length}, sroads={self.sroads})"

    @property
    def car_sorter(self):
        return self.sroads[-1].car_sorter

    @car_sorter.setter
    def car_sorter(self, car_sorter):
        self.sroads[-1].car_sorter = car_sorter
