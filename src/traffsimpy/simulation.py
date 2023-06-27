from time import time, strftime

import pygame.event
from matplotlib import pyplot as plt

from .components import *
from .drawing import *


class Simulation:
    def __init__(self, title: str = "TraffSimPy", width: int | None = None, height: int | None = None):
        """Simulation du trafic.

        Args:
            title: titre de la fenêtre
            width: largeur de la fenêtre, en pixels. Détectée
                automatiquement si non fourni, puis récupérable avec
                ``Simulation.size[0]``.
            height: hauteur de la fenêtre, en pixels. Détectée
                automatiquement si non fourni, puis récupérable avec
                ``Simulation.size[1]``.
        """
        self.id = 0
        sc.dynamic_data = sc.def_settings["dynamic_data"]
        sc.dynamic_data["ids"] = {0: self}
        pygame.init()  # initialisation de pygame

        self.title = title  # titre de la fenêtre
        pygame.display.set_caption(title)  # modification du titre de la fenêtre

        monitor_info = pygame.display.Info()  # récuparation de la taille de l'écran si non fournie (fonctionne plutôt mal)
        if width is None:
            width = monitor_info.current_w
        if height is None:
            height = monitor_info.current_h
        self.size = width, height  # taille de la fenêtre

        self.t = 0.0  # suivi du temps
        self.FPS = sc.fps  # images par seconde
        self.dt = 1 / sc.fps  # pas de temps
        self.speed_ajusted_fps = sc.fps * sc.speed  # FPS ajusté pour la vitesse de la simulation
        self.speed = sc.speed  # vitesse de la simulation
        self.over = self.paused = False  # si la simulation est finie ou en pause
        self.duration = INF  # durée de la simulation, définie dans self.start_loop() par l'utilisateur

        self.roads = []  # liste des routes
        self.road_graph = {}  # graphe des routes
        self.heavy_traffic_area = (npz(2), INF)  # zone où get_bumping_cars est utilisé

        self.surface = pygame.display.set_mode(self.size)  # création de la fenêtre
        self.clock = pygame.time.Clock()  # création de l'horloge pygame
        self.bg_color = sc.background_color  # couleur d'arrière-plan de la fenêtre
        self.surface.fill(self.bg_color)  # coloriage de l'arrière-plan

        self.FONT = pygame.font.Font(sc.font_path, sc.font_size)  # police d'écriture des informations
        self.SMALL_FONT = pygame.font.Font(sc.font_path, round(sc.car_width * sc.scale * 0.8))  # pour les voitures
        self.ARROW_IMG = pygame.image.load(sc.arrow_path).convert_alpha()  # chargement de l'image de flèche
        self.SMALL_ARROW = pygame.transform.smoothscale(self.ARROW_IMG, (
            sc.car_width * sc.scale * 0.8, sc.car_width * sc.scale * 0.8))

        # générer l'image de flèche avec l'angle de la route est très long, on le fera qu'une fois au début de
        # start_loop() et on la stockera sous deux tailles dans ce dictionnaire
        self.roads_rotated_arrows = {}

        self.off_set = npz(2)  # décalage par rapport à l'origine, pour bouger la simulation
        self.dragging = False  # si l'utilisateur est en train de bouger la simulation
        self.mouse_last = npz(2)  # dernières coordonnées de la souris

    def rc_to_sc(self, coordinates: Coordinates | None, is_vect: bool = False):
        """Convertie des coordonnées naturelles (abscisses vers la droite, ordonnées vers le haut) en coordonnées
        de la simulation (abscisses vers la droite, ordonnées vers le bas), et en nparray.
        """
        if isinstance(coordinates, (float, int, type(None))):
            return coordinates

        x, y = coordinates

        if is_vect:
            return npa([x, -y])
        else:
            return npa([x, self.size[1] - y])

    def start_loop(self, duration: float):
        """Lance la boucle de la simulation, en actualisant chaque élément et en les affichant ``FPS`` fois par
        seconde, pendant une durée ``duration``.
        """
        self.duration = duration

        # initialisation des images de flèches orientées dans le sens des routes
        for road in self.roads:
            arrow_width = road.width * 0.7
            arrow = pygame.transform.smoothscale(self.ARROW_IMG, (arrow_width, arrow_width))

            if road.with_arrows:
                period = sc.road_arrow_period  # période spatiale des flèches
                n = round(road.length / period)  # nombre de flèches pour la route
                coordinates = []

                for i in range(n):
                    arrow_coord = road.dist_to_pos((i + 0.5) * period)  # "+ O.5" pour centrer les flèches sur la longueur
                    coordinates.append(arrow_coord)
            else:
                coordinates = []

            road_arrows = {"small_arrow": pygame.transform.rotate(self.SMALL_ARROW, road.angle),
                           "large_arrow": pygame.transform.rotate(arrow, road.angle),
                           "coordinates": coordinates}

            self.roads_rotated_arrows[road.id] = road_arrows

        while not self.over:  # tant que la simulation n'est pas terminée
            for event in pygame.event.get():  # on regarde les dernières actions de l'utilisateur
                self.manage_event(event)

            self.surface.fill(self.bg_color)  # on efface tout

            self.show_heavy_traffic_area()  # on affiche la zone où les collisions sont détectées
            self.show_roads(self.roads)  # on affiche les routes

            if self.paused:  # si en pause
                for road in self.roads:
                    for car in road.cars:
                        self.show_car(car)  # on affiche les voitures de la route
                    for sensor in road.sensors:
                        self.show_sensor(sensor)  # on affiche les capteurs de la route
                    self.show_sign(road.sign)  # on affiche le feu/panneau stop
                self.show_info(self.info_to_show)  # on affiche les informations
                pygame.display.update()  # actualisation de la fenêtre
                self.clock.tick(self.FPS)  # pause d'une durée dt
                continue  # saute la suite de la boucle et passe à l'itération suivante

            # mise à jour des interactions entre les voiture
            if sc.use_hitboxes:
                for car1, car2 in self.pair_of_cars_maybe_interacting():
                    self.manage_cars_interaction(car1, car2)

            # on actualise la simulation route par route
            for road in self.roads:
                # affichage des voitures de la route et mise à jour des prévisions de collision
                for car in road.cars:
                    self.show_car(car)

                # affichage des capteurs de la route
                for sensor in road.sensors:
                    self.show_sensor(sensor)

                # affichage de l'élément de signalisation (feu/panneau stop) de la route
                self.show_sign(road.sign)

                # actualisation des objets de la route
                road_leaders = self.get_road_leaders(road, avg=sc.average_leaders)
                road.update_cars(self.dt, road_leaders)
                road.update_sensors(self.t)
                road.update_sign(self.t)

                # éventuelle création d'une nouvelle voiture au début de la route
                if road.car_factory.freq_func is not None:
                    new_car = road.car_factory.factory({"t": self.t}, {"t": self.t})
                    road.new_car(new_car)

            self.t += self.dt  # actualisation du suivi du temps
            self.show_info(self.info_to_show)  # affiche les informations
            pygame.display.update()  # actualisation de la fenêtre
            self.clock.tick(self.speed_ajusted_fps)  # pause d'une durée dt
            self.over = (self.t >= duration) or self.over  # arrêt si le temps est écoulé ou si l'utilisateur quitte

    def start_loop_no_display(self, duration: float, progression: bool = False):
        """Lance la boucle de la simulation pendant une durée ``duration``, sans affichage et à la vitesse maximum."""
        self.duration = duration

        while self.t <= duration:  # tant que la simulation n'est pas terminée
            if sc.use_hitboxes:
                for car1, car2 in self.pair_of_cars_maybe_interacting():
                    self.manage_cars_interaction(car1, car2)

            # on actualise la simulation route par route
            for road in self.roads:
                # actualisation des objets de la route
                road_leaders = self.get_road_leaders(road, avg=sc.average_leaders)
                road.update_cars(self.dt, road_leaders)
                road.update_sensors(self.t)
                road.update_sign(self.t)

                # éventuelle création d'une nouvelle voiture au début de la route
                if road.car_factory.freq_func is not None:
                    new_car = road.car_factory.factory({"t": self.t}, {"t": self.t})
                    road.new_car(new_car)

            self.t += self.dt  # actualisation du suivi du temps

            if progression:
                print(f"\rSimulation {tbold(self.title)} à {round(100 * self.t / self.duration)} %", end="")

        print("\r")

    def run(self, duration: float = INF, display=True):
        """Lance la simulation."""
        if duration <= 0:
            raise ValueError("La simulation doit avoir une durée strictement positive !")

        if not self.roads:
            raise NotImplementedError("Aucune route n'a été définie. Vous pouvez définir des routes avec create_roads().")

        try:
            starting_time = time()

            if display:
                self.start_loop(duration)
            else:
                self.start_loop_no_display(duration, True)

            real_duration = time() - starting_time
            simulation_speed = self.t / real_duration
            end_message = f"Simulation {tbold(self.title)} ({self.t:.4f}s) terminée au bout de {real_duration:.4f}s, soit une vitesse de simulation de {simulation_speed:.4f}.\n"
            print(end_message)
        except Exception as exception:
            print_error(exception)
        finally:
            self.print_simulation_info()

    def print_simulation_info(self):
        """Affiche l'ensemble des objets de la simulation et leurs principaux attributs dans la sortie standard."""
        if sc.print_detailed_logs:
            print(f"\n{tbold('--- Simulation Info ---')}\n\n{self.size = }\n{self.t = }\n{self.FPS = }\n{self.dt = }\n{self.speed = }\n{self.speed_ajusted_fps = }\n{self.paused = }\n{self.over = }\n{self.dragging = }\n{self.off_set = }\n{self.road_graph = }\n")
            for road in self.roads:
                print(f"\n{road} :\n    Sign : {road.sign}\n    Cars :")
                for car in road.cars:
                    print(f"        {car}")
                print("    Sensors :")
                for sensor in road.sensors:
                    print(f"        {sensor}")
                print(f"    CarFactory : {road.car_factory}\n    CarSorter : {road.car_sorter}\n\n")

    @property
    def info_to_show(self):
        """Renvoie les informations à afficher sur la fenêtre : horloge, vitesse, en pause ou non."""
        str_speed = self.speed if self.speed != int(self.speed) else int(self.speed)
        duration_perc = f" = {int(self.t / self.duration * 100):>2}%" if self.duration < INF else ""
        return f"t = {round(self.t, 2):<7} = {int(self.t // 60):>02}m{int(self.t) % 60:02}s{duration_perc} | vitesse = ×{str_speed:<4} | {'en pause' if self.paused else 'en cours'}"

    def manage_event(self, event):
        """Gère les conséquences en cas d'un certain évènement pygame, c'est-à-dire une action de l'utilisateur (pause, changement de vitesse, déplacement...)."""
        if event.type == pygame.QUIT:  # arrêter la boucle quand la fenêtre est fermée
            self.over = True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # quitte quand on appuie sur escape
                self.over = True
            elif event.key == pygame.K_SPACE:
                # met la simulation en pause quand on appuie sur espace
                self.paused = not self.paused
                if self.paused:  # si on passe de "en cours" à "en pause", afficher les infos
                    self.print_simulation_info()
                    if sc.sensor_print_res_at_pause:
                        self.print_sensors_results()
                    if sc.sensor_export_res_at_pause:
                        self.export_sensors_results()
            elif event.key in (pygame.K_LEFT, pygame.K_DOWN) and self.speed >= 0.5:
                # si l'utilisateur appuie sur la flèche gauche ou bas
                self.speed = round(self.speed / 2, 2)
                self.speed_ajusted_fps = round(self.speed_ajusted_fps / 2, 2)
            elif event.key in (pygame.K_RIGHT, pygame.K_UP) and 2 * self.speed <= sc.max_speed:
                # si l'utilisateur appuie sur la flèche droite ou haut, accélérer jusqu'à MAX_SPEED
                self.speed = round(self.speed * 2, 2)
                self.speed_ajusted_fps = round(self.speed_ajusted_fps * 2, 2)
            elif event.key == pygame.K_RETURN:
                # si l'utilisateur appuie sur entrer, recentrer la fenêtre
                self.off_set = (0, 0)
            elif event.key == pygame.K_s:
                # si l'utilisateur appuie sur S, enregistrer la fenêtre
                filename = f"screenshot_{self.title}_{self.t}." + sc.screenshot_type
                pygame.image.save(self.surface, filename)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # si l'utilisateur clique
            self.mouse_last = npa(pygame.mouse.get_pos()) - self.off_set
            self.dragging = True

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # bouge la simulation
            self.off_set = npa(pygame.mouse.get_pos()) - self.mouse_last

        elif event.type == pygame.MOUSEBUTTONUP:
            # si l'utilisateur ne clique plus
            self.dragging = False

    def create_road(self, **kw):
        """Créer une route, renvoie la route."""
        # récupération des paramètres communs à tous les types de route
        road_type = kw.get("type", kw.get("t", "road"))  # type ou son alias t, par défaut road
        start = kw.get("start", kw.get("s", (0, 0)))  # start ou son alias s, par défaut (0, 0)
        end = kw.get("end", kw.get("e", self.size))  # end ou son alias e, par défaut (height, width) de la fenêtre
        v_max = kw.get("v_max", sc.v_max)  # v_max, par défaut sc.v_max
        color = kw.get("color", kw.get("c", sc.road_color))  # color ou son alias c, par défaut sc.road_color
        with_arrows = kw.get("with_arrows", kw.get("wa", True))  # with_arrows ou son alias wa, par défaut True
        priority = kw.get("priority", kw.get("p", 0))  # priority ou son alias p, par défaut 0
        heavily_traveled = kw.get("heavily_traveled", kw.get("ht", False))  # heavily_traveled ou son alias ht, par défaut False
        obj_id = kw.get("id")  # id, par défaut None

        # conversion des coordonnées classiques en coordonnées pygame (ne change pas les int et float)
        start, end = self.rc_to_sc(start), self.rc_to_sc(end)

        # mise à l'échelle
        v_max *= sc.scale

        if isinstance(start, int):  # si l'argument start est un id de route
            rstart = get_by_id(start, None)
            if rstart is None:  # si l'id n'est pas utilisé
                raise ValueError(f"La route d'identifiant {start} n'a pas encore été définie mais est requise pour le début de la route {kw}.")
            start = rstart.end
            vdstart = rstart.vd
        else:
            vdstart = kw.get("vdstart", kw.get("vds", kw.get("vs")))  # vdstart ou ses alias vds et vs
            vdstart = self.rc_to_sc(vdstart, is_vect=True)  # conversion en coordonnées pygame

        if isinstance(end, int):  # si l'argument end est un id de route
            rend = get_by_id(end, None)
            if rend is None:  # si l'id n'est pas utilisé
                raise ValueError(f"La route d'identifiant {end} n'a pas encore été définie mais est requise pour la fin de la route {kw}.")
            end = rend.start
            vdend = rend.vd
        else:
            vdend = kw.get("vdend", kw.get("vde", kw.get("ve")))  # vdend ou ses alias vde et ve
            vdend = self.rc_to_sc(vdend, is_vect=True)  # conversion en coordonnées pygame

        if road_type in ["road", "r"]:  # si on crée une route droite
            car_factory = kw.get("car_factory", kw.get("cf"))  # car_factory ou son alias cf, par défaut None
            sign = kw.get("sign", kw.get("sg"))  # sign ou son alias sg, par défaut None
            sensors = kw.get("sensors", kw.get("srs"))  # sensors ou son alias srs, par défaut None
            road = Road(start=start, end=end, color=color, v_max=v_max, with_arrows=with_arrows, priority=priority,
                        heavily_traveled=heavily_traveled, car_factory=car_factory, sign=sign, sensors=sensors,
                        obj_id=obj_id)

            self.roads.append(road)

        elif road_type in ["arcroad", "arc", "a"]:  # si on crée une route courbée
            n = kw.get("n", sc.arcroad_num_of_sroads)  # n, par défaut sc.arcroad_num_of_sroads
            road = ArcRoad(start=start, end=end, vdstart=vdstart, vdend=vdend, n=n, v_max=v_max,
                           with_arrows=with_arrows, heavily_traveled=heavily_traveled, color=color, priority=priority,
                           obj_id=obj_id)

            for sroad in road.sroads[::-1]:
                self.roads.append(sroad)

        else:
            raise ValueError(f'Le type de route doit être parmi "road", "r", "arcroad", "arc", "a" ou "", pas "{kw["type"]}".')

        return road

    def create_roads(self, road_list: list[dict]):
        """Créer des routes, renvoie la liste des routes.

        Les éléments de ``road_list`` sont des dictionnaires de la forme :\n
        - pour une route droite, ``{"id": int (optionnel), "type": "road", "start": (float, float) | int, "end": (float, float) | int, "car_factory": CarFactory (optionnel), "v_max": float (optionnel), "sign": TrafficLight | StopSign (optionnel), "sensors": Sensor (optionnel), "color": (int, int, int) (optionnel), "with_arrows": bool (optionnel)}``
        - pour une route courbée, ``{"id": int (optionnel), "type": "arcroad", "start": (float, float) | int, "vdstart": (float, float), "end": (float, float) | int, "vdend": (float, float), "car_factory": CarFactory (optionnel), "v_max": float (optionnel), "color": (int, int, int) (optionnel), "n": int (optionnel)}``

        avec :\n
        - ``id`` l'éventuel l'identifiant de la route
        - ``start`` les coordonnées du début de la route (éventuellement négatives), ou l'identifiant d'une route déjà définie dont la fin servira de début
        - ``end`` les coordonnées de la fin de la route (éventuellement négatives), ou l'identifiant d'une route déjà définie dont le début servira de fin
        - ``car_factory`` l'éventuel CarFactory
        - ``v_max`` l'éventuelle limite de vitesse (en m/s) de la route, ``V_MAX`` par défaut
        - ``color`` la couleur de la route, ``ROAD_COLOR`` par défaut
        - ``vdstart`` pour arcroad, si ``start`` est un couple de coordonnées, vecteur directeur du début
        - ``vdend`` pour arcroad, si ``end`` est un couple de coordonnées, vecteur directeur de la fin
        - ``n`` pour arcroad, l'éventuel nombre de routes droites la composant, par défaut ``N_ARCROAD``
        - ``sign`` pour road, l'éventuel TrafficLight ou StopSign
        - ``sensors`` pour road, le ou les éventuels capteurs de la route
        - ``with_arrow`` pour road, si des flèches seront affichées sur la route dans le sens de la circulation
        """
        return [self.create_road(**road) for road in road_list]

    def set_road_graph(self, graph: dict):
        """Définie le graphe des routes de la simulation. Prend en argument le graphe des routes, qui est un dictionnaire
        qui à l'identifiant d'une route associe une des choses suivantes :

        - l'identifiant d'une autre route
        - un dictionnaire associant l'identifiant d'une autre route à la probabilité d'aller sur cette route
        - une fonction f(t: float) -> int qui au temps **d'arrivée** de la voiture sur la route associe l'identifiant d'une autre route
        - None ou {} pour supprimer les voitures qui sortent de la route (ne pas inclure l'identifiant de la route dans le dictionnaire a le même effet)

        Args:
            graph: graphe des routes
        """
        processed_graph = {}

        def process_next_roads(nrs):
            """Traite nrs pour retirer les dépendances en ArcRoad."""
            if isinstance(nrs, int) and isinstance(next_road := get_by_id(nrs), ArcRoad):
                return next_road.sroads[0].id

            elif isinstance(next_roads, dict):
                processed_next_roads = {}
                for next_road_id in nrs:
                    proba = nrs[next_road_id]
                    if isinstance(next_road := get_by_id(next_road_id), ArcRoad):
                        processed_next_roads[next_road.sroads[0].id] = proba
                    else:
                        processed_next_roads[next_road_id] = proba
                return processed_next_roads

            else:
                return nrs

        for road_id in graph:
            road = get_by_id(road_id)
            next_roads = graph[road_id]

            if isinstance(road, ArcRoad):
                processed_graph[road.sroads[-1].id] = process_next_roads(next_roads)
                for i in range(road.n - 1):
                    processed_graph[road.sroads[i].id] = road.sroads[i + 1].id

            processed_graph[road_id] = process_next_roads(next_roads)

        for road_id in processed_graph:
            road = get_by_id(road_id)
            road.car_sorter = CarSorter(processed_graph[road_id])

            if road.car_sorter.method == "user func":
                processed_graph[road_id] = None

            elif isinstance(processed_graph[road_id], int):
                processed_graph[road_id] = {processed_graph[road_id]: 1}

        self.road_graph = processed_graph

    def set_heavy_traffic_area(self, center: Union[tuple[float, float], Coordinates] = None, radius: float = INF):
        """Définie la zone circulaire où le trafic sera probablement dense et où la simulation utilisera les hitbox et
        hurtbox des voitures pour éviter les collisions. La détection de collision sera automatiquement activée, même si
        ``USE_BUMPING_BOXES = False``.

        Args:
            center: centre du disque décrivant la zone, centre de la
                fenêtre par défaut
            radius: rayon du disque décrivant la zone, en **pixels**,
                +inf par défaut
        """
        sc.use_hitboxes = True

        if center is None:
            center = self.size[0] / 2, self.size[1] / 2

        self.heavy_traffic_area = (self.rc_to_sc(center), radius)

    def show_info(self, info: str):
        """Affiche des informations en haut à gauche de la fenêtre et l'échelle si besoin."""
        if sc.show_infos:
            text_width, text_height = self.FONT.size(info)
            draw_rect(self.surface, sc.info_background_color, npz(2), text_width + 30, text_height + 20)
            draw_text(self.surface, sc.font_color, npa((10, 10)), info, self.FONT)

        if sc.show_scale:
            self.show_scale()

    def show_scale(self):
        """Affiche l'échelle en bas à gauche de la fenêtre."""
        _, h = self.size
        n = 10
        x, y = 30, h - 40
        text = f"{n * sc.scale}px = {n}m"
        tw, th = self.FONT.size(text)
        draw_rect(self.surface, BLACK, npa((x, y)), n * sc.scale, 10)  # affiche la barre de n*SCALE pixels
        for i in range(1, n, 2):  # affiche les graduations
            draw_rect(self.surface, self.bg_color, npa((x + i * sc.scale, y + 1)), sc.scale - 2 / n, 8)
        draw_text(self.surface, BLACK, npa((x + (n * sc.scale - tw) / 2,
                                            y - th - 2)), text, self.FONT)  # affiche la description

    def show_car(self, car: Car):
        """Affiche une voiture."""
        if sc.car_show_hitboxes:  # si on affiche les zones de collision
            brightness = 1.1 if is_inside_circle(car.pos, self.heavy_traffic_area) else 0.9
            brighten = lambda color: min(int(color * brightness), 255)

            r, g, b = car.color

            side_bumper_color = (brighten(r * 1.2), brighten(g), brighten(b))  # même couleur plus claire et plus rouge
            draw_polygon(self.surface, side_bumper_color, car.side_bumper_hurtbox, self.off_set)

            front_bumper_color = (brighten(r), brighten(g * 1.2), brighten(b))  # même couleur plus claire et plus verte
            draw_polygon(self.surface, front_bumper_color, car.front_bumper_hitbox, self.off_set)

        if sc.car_show_bounding_boxes:
            aabb_vertices = car.aabb[0], npa([car.aabb[0][0], car.aabb[1][1]]), car.aabb[1], npa([car.aabb[1][0], car.aabb[0][1]])
            draw_empty_polygon(self.surface, car.color, aabb_vertices, self.off_set)

        if sc.car_show_leader_links:
            if car.soon_colliding_cars:
                for leader in car.soon_colliding_cars:
                    draw_line(self.surface, car.color, car.pos, leader.pos, self.off_set)
            else:
                for leader, *_ in car.leaders:
                    draw_line(self.surface, car.color, car.pos, leader.pos, self.off_set)

        if sc.car_speed_coded_color:  # si la couleur de la voiture dépend de sa vitesse
            car_color = red_to_blue_gradient(car.v / (sc.v_max * sc.scale))
        else:
            car_color = car.color

        draw_polygon(self.surface, car_color, car.vertices,
                     self.off_set)  # affiche le rectangle qui représente la voiture

        if sc.car_show_direction:  # si on affiche la direction de la voiture
            rotated_arrow = self.roads_rotated_arrows[car.road.id]["small_arrow"]
            draw_image(self.surface, rotated_arrow, car.road.dist_to_pos(car.d), self.off_set)

        roof_text = ""

        if sc.car_show_speed_ms:  # si on affiche la vitesse de la voiture en m/s
            text = str(round(car.v / sc.scale))
            roof_text += text
        if sc.car_show_speed_kmh:  # si on affiche la vitesse en km/h
            text = str(round(3.6 * car.v / sc.scale))
            roof_text += ("|" if roof_text else "") + text
        if sc.car_show_id:  # si on affiche l'id de la voiture
            text = str(car.id)
            roof_text += ("|" if roof_text else "") + text
        if roof_text:
            text_width, text_height = self.SMALL_FONT.size(roof_text)
            x = car.pos[0] - text_width / 2
            y = car.pos[1] - text_height / 2
            draw_text(self.surface, sc.font_color, npa((x, y)), roof_text, self.SMALL_FONT, off_set=self.off_set)

    def show_roads(self, road_list: Sequence[Road | ArcRoad]):
        """Affiche des routes."""
        for road in road_list:  # on affiche d'abord les rectangles des routes
            draw_polygon(self.surface, road.color, road.vertices, self.off_set)

        for road in road_list:  # puis les flèches
            if road.with_arrows:
                rotated_arrows = self.roads_rotated_arrows[road.id]

                for arrow_coord in rotated_arrows["coordinates"]:
                    draw_image(self.surface, rotated_arrows["large_arrow"], arrow_coord, self.off_set)

    def show_sign(self, sign: TrafficLight | StopSign):
        """Affiche un élément de signalisation."""
        if isinstance(sign, TrafficLight) and not sign.static:
            color = {0: sc.tl_red, 1: sc.tl_orange, 2: sc.tl_green}[sign.state]
            draw_polygon(self.surface, color, sign.vertices, self.off_set)
        elif isinstance(sign, StopSign):
            draw_polygon(self.surface, sc.ss_color, sign.vertices, self.off_set)

    def show_sensor(self, sensor: Sensor):
        """Affiche un capteur."""
        draw_polygon(self.surface, sc.sensor_color, sensor.vertices, self.off_set)

    def show_heavy_traffic_area(self):
        """Affiche la zone où les collisions sont gérées."""
        center, radius = self.heavy_traffic_area
        if sc.show_heavy_traffic_area and radius < INF:
            da = lambda color: int(color * 0.93)
            r, g, b = self.bg_color
            draw_circle(self.surface, (da(r), da(g), da(b)), center, radius, self.off_set)

    def compute_sensors_results(self, *sensors_id, since=0, how_many=INF):
        """Calcule les résultats de capteurs."""
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    sensor.compute_results(since, how_many)
        else:
            for sensor_id in sensors_id:
                sensor = get_by_id(sensor_id)
                sensor.compute_results(since, how_many)

    def print_sensor_results(self, sensor: Sensor):
        """Affiche les résultats d'un capteur dans la sortie standard."""
        res_str = sensor.results()

        if res_str.strip():
            text = tbold(f"Résulats à t={round(self.t, 2)}s de {sensor} :\n") + res_str + "\n"
            print(text)

    def print_sensors_results(self, *sensors_id):
        """Affiche les résulats de capteurs dans la sortie standard."""
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    self.print_sensor_results(sensor)
        else:
            for sensor_id in sensors_id:
                sensor = get_by_id(sensor_id)
                self.print_sensor_results(sensor)

    def export_sensor_results(self, sensor: Sensor, describe: bool):
        """Exporte les résultats d'un capteur dans un fichier Excel .xlsx."""
        file_name = f"{sc.sensor_file_prefix}{self.title}_capteur{sensor.id}_{strftime('%H%M%S_%d%m%y')}.xlsx"
        sheet_name = f"{self.title} ({round(self.t, 2)}s) capteur {sensor.id}"
        sensor.export_results(file_name, sheet_name, describe)

    def export_sensors_results(self, *sensors_id, describe: bool = True):
        """Exporte les résultats de capteurs dans des fichiers Excel .xlsx."""
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    self.export_sensor_results(sensor, describe)
        else:
            for sensor_id in sensors_id:
                sensor = get_by_id(sensor_id)
                self.export_sensor_results(sensor, describe)

    def plot_sensors_results(self, *sensors_id, **plot_kwargs):
        """Affiche les résulats de capteurs sous forme d'un graphe de fonctions."""
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    sensor.plot_results(**plot_kwargs)

        else:
            for sensor_id in sensors_id:
                if isinstance(sensor_id, int):
                    get_by_id(sensor_id).plot_results(**plot_kwargs)
                else:
                    s_id, x = sensor_id
                    get_by_id(s_id).plot_results(x=x, **plot_kwargs)

        plt.show()

    def get_road_leaders(self, road, avg=False):
        """Renvoie les éventuels leaders de la première voiture de la route, dans une liste de tuples de la forme
        ``(voiture, distance, proba)``.

        Args:
            road: route à traiter
            avg: si le parcours se fait selon toutes les prochaines routes possibles ou selon la prochaine route de la
                première voiture
        """
        if not road.cars:  # si la route n'a pas de voitures, le résultat du parcours ne sera pas utilisé
            return []

        already_seen_roads_id = {}  # routes déjà vues
        leaders = []  # résultat du parcours : liste de tuples (voiture, distance, proba)

        def searcher(start_road: Road, d_traveled: float, p: float):
            """Parcours en profondeur des routes de la simulation depuis la route r. Rempli la liste leaders lorsque
            la route possède au moins une voiture ou un élément de signalisation actif, cherche plus loin sinon.

            Args:
                start_road: départ du parcours
                d_traveled: distance déjà parcourue
                p: probabilité d'arriver sur cette route
            """
            if start_road.id in already_seen_roads_id:
                # si on est déjà passé sur la route, on fait rien
                return
            else:
                # sinon on la marque comme déjà vue
                already_seen_roads_id[start_road.id] = 1

            if start_road.cars:
                # si la route possède au moins une voiture, on prend la dernière
                last_car = start_road.cars[-1]
                leaders.append((last_car, d_traveled + last_car.d - last_car.length / 2, p))

            elif start_road.sign.dummy_car is not None:
                # si elle a un élément de signalisation actif, on le prend lui
                leaders.append((start_road.sign.dummy_car, d_traveled + start_road.length, p))

            else:
                # sinon, on cherche plus loin
                next_rds_ids = self.road_graph.get(start_road.id)
                if next_rds_ids is None:  # si pas de prochaine route, on s'arrête
                    return

                else:
                    for next_rd_id in next_rds_ids:
                        next_p = next_rds_ids[next_rd_id]
                        searcher(get_by_id(next_rd_id), d_traveled + start_road.length, p * next_p)

        if avg:
            next_roads_ids = self.road_graph.get(road.id)

            if next_roads_ids is not None:
                for next_road_id in next_roads_ids:
                    proba = next_roads_ids[next_road_id]
                    searcher(get_by_id(next_road_id), 0, proba)

        else:
            first_car: Car = road.cars[0]

            if first_car.next_road is None:
                leaders = self.get_road_leaders(road, True)
            else:
                searcher(first_car.next_road, 0, 1)

        return leaders

    def pair_of_cars_maybe_interacting(self):
        """Renvoie la liste des couples de voitures en potentielle interaction (bientôt en collision, etc...), en
        utilisant des conditions nécessaires et peu coûteuses à calculer, mais pas suffisantes. Correspond à la phase
        "broad" dans la détection de collisions.
        """
        # construction de la liste des voitures de la simulation dans la zone de trafic dense
        cars = []
        for road in self.roads:
            for car in road.cars:
                if road.is_heavily_traveled or is_inside_circle(car.pos, self.heavy_traffic_area):
                    cars.append(car)

        # contruction des couples
        pair_of_cars = []
        already_seen_pairs = {}  # couples d'identifiants déjà rencontrés
        for car1 in cars:
            for car2 in cars:
                if car1 == car2 or (car1.id, car2.id) in already_seen_pairs:
                    continue

                already_seen_pairs[(car1.id, car2.id)] = True
                already_seen_pairs[(car2.id, car1.id)] = True

                dist = distance(car1.pos, car2.pos)
                car1_max_size = car1.length / 2 + car1.delta_d_min / 2 + car1.v * car1.t_react
                car2_max_size = car2.length / 2 + car2.delta_d_min / 2 + car2.v * car2.t_react

                if dist >= car1_max_size + car2_max_size:
                    # si les voitures sont trop éloignées, aucune chance d'interaction
                    continue

                # on vérifie si les boîtes englobantes droites (AABB) des deux voitures s'intersectent

                (min_x1, min_y1), (max_x1, max_y1) = car1.aabb
                (min_x2, min_y2), (max_x2, max_y2) = car2.aabb

                if min_x1 > max_x2 or min_y1 > max_y2:
                    continue

                if min_x2 > max_x1 or min_y2 > max_y1:
                    continue

                # si on arrive là, c'est que les deux voitures sont peut être en interaction
                pair_of_cars.append((car1, car2))

        return pair_of_cars

    @staticmethod
    def manage_cars_interaction(car1: Car, car2: Car):
        """Détermine quelle interaction deux voitures ont entre elles, c'est-à-dire s'il l'une va rentrer dans l'autre,
        si elle vont toutes les deux se percuter et qui a la priorité sur qui. Met à jour la liste
        ``soon_colliding_cars`` de la voiture concernée. Correspond à la phase "narrow" dans la détection de
        collisions."""
        c1mcwc2 = car1.may_collide_with(car2)
        c2mcwc1 = car2.may_collide_with(car1)

        if c1mcwc2 and c2mcwc1:
            if car1.has_priority_over(car2):
                car2.soon_colliding_cars.append(car1)
            else:
                car1.soon_colliding_cars.append(car2)

        elif c1mcwc2:
            car1.soon_colliding_cars.append(car2)

        elif c2mcwc1:
            car2.soon_colliding_cars.append(car1)

        elif car1.might_collide_with(car2):
            if car1.has_priority_over(car2):
                car2.soon_colliding_cars.append(car1)
            else:
                car1.soon_colliding_cars.append(car2)
