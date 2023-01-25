import traceback
from time import time, strftime

import pygame.event
from matplotlib import pyplot as plt

from .components import *
from .drawing import *
from .ressources import *


class Simulation:
    def __init__(self, title: str = "Traffic Simulation", width: int = 1440, height: int = 820):
        """
        Simulation du trafic.

        :param title: titre de la fenêtre
        :param width: largeur de la fenêtre, en pixels
        :param height: hauteur de la fenêtre, en pixels
        """
        self.id = new_id(self, 0)
        self.title = title  # titre de la fenêtre
        self.size = npa((width, height))  # taille de la fenêtre
        self.t = 0.0  # suivi du temps
        self.FPS = s.FPS  # images par seconde
        self.dt = 1/self.FPS  # pas de temps
        self.speed_ajusted_fps = self.FPS / s.SPEED  # pas de temps ajusté pour la vitesse de la simulation
        self.speed = s.SPEED  # vitesse de la simulation
        self.over = self.paused = False  # si la simulation est finie ou en pause
        self.duration = INF  # durée de la simulation, définie dans self.start_loop() par l'utilisateur

        self.roads = []  # liste des routes
        self.road_graph = {}  # graphe des routes
        self.bumping_zone = (npz(2), INF)  # zone où get_bumping_cars est utilisé

        pygame.init()  # initialisation de pygame
        pygame.display.set_caption(title)  # modification du titre de la fenêtre

        self.surface = pygame.display.set_mode(self.size)  # création de la fenêtre
        self.clock = pygame.time.Clock()  # création de l'horloge pygame
        self.bg_color = s.BACKGROUND_COLOR  # couleur d'arrière plan de la fenêtre
        self.surface.fill(self.bg_color)  # coloriage de l'arrière plan
        self.FONT = pygame.font.Font(s.FONT_PATH, s.FONT_SIZE)  # police d'écriture des informations
        self.SMALL_FONT = pygame.font.Font(s.FONT_PATH, round(s.CAR_WIDTH * 0.8))  # pour les voitures

        arrow = pygame.image.load(s.ARROW_PATH).convert_alpha()  # chargement de l'image de flèche
        self.ROAD_ARROW = pygame.transform.smoothscale(arrow, (s.ROAD_WIDTH*0.7, s.ROAD_WIDTH*0.7))  # ajustement de la taille des flèches pour les routes
        self.CAR_ARROW = pygame.transform.smoothscale(arrow, (s.CAR_WIDTH*0.8, s.CAR_WIDTH*0.8))  # pour les voitures

        self.off_set = npz(2)  # décalage par rapport à l'origine, pour bouger la simulation
        self.dragging = False  # si l'utilisateur est en train de bouger la simulation
        self.mouse_last = npz(2)  # dernière coordonnées de la souris

    def rc_to_sc(self, coordinates: Vecteur | tuple[float, float]):
        """Convertie des coordonnées naturelles (abscisses vers la droite, ordonnées vers le haut) en coordonnées
        de la simulation (abscisses vers la droite, ordonnées vers le bas)."""
        if isinstance(coordinates, (tuple, list)):
            x, y = coordinates
            _, h = self.size
            return x, h - y
        else:
            return coordinates

    def start_loop(self, duration: float):
        """Ouvre une fenêtre et lance la simulation."""
        self.duration = duration

        while not self.over:  # tant que la simulation n'est pas terminée
            for event in pygame.event.get():  # on regarde les dernières actions de l'utilisateur
                self.manage_event(event)

            self.surface.fill(self.bg_color)  # efface tout

            self.show_bumping_zone()  # affiche la zone où les collisionns sont détectées
            self.show_roads(self.roads)  # affiche les routes

            if self.paused:  # si en pause
                for road in self.roads:
                    for car in road.cars:
                        self.show_car(car)  # affichage des voitures de la route
                    for sensor in road.sensors:
                        self.show_sensor(sensor)
                    self.show_traffic_light(road.traffic_light)
                self.show_info(self.info_to_show)  # affiche les informations
                pygame.display.flip()  # actualisation de la fenêtre
                self.clock.tick(self.FPS)  # pause d'une durée dt
                continue  # saute la suite de la boucle et passe à l'itération suivante

            for road in self.roads:
                for car in road.cars:
                    self.show_car(car)  # affichage des voitures de la route
                    car.leaders = self.get_bumping_cars(car)

                # affiche les capteurs
                for sensor in road.sensors:
                    self.show_sensor(sensor)

                self.show_traffic_light(road.traffic_light)  # affichage du feu

                # actualisation des coordonnées des voitures de la route, des capteur et du feu
                road.update_cars(dt=self.dt, leaders=self.get_leaders(road, avg=s.GET_LEADERS_METHOD_AVG))

                # actualise les capteurs
                road.update_sensors(self.t)

                # actualise le feu
                road.update_traffic_light(self.t)

                # éventuelle création d'une nouvelle voiture au début de la route
                args_crea = {"t": self.t}
                args_fact = {"t": self.t, "last_car": road.cars[-1] if road.cars else None}
                new_car = road.car_factory.factory(args_crea=args_crea, args_fact=args_fact)
                road.new_car(new_car)

            self.t += self.dt  # actualisation du suivi du temps
            self.show_info(self.info_to_show)  # affiche les informations
            pygame.display.flip()  # actualisation de la fenêtre
            self.clock.tick(self.speed_ajusted_fps)  # pause d'une durée dt
            self.over = (self.t >= duration) or self.over  # arrêt si le temps est écoulé ou si l'utilisateur quitte

    def start(self, duration: float = INF):
        """Ouvre une fenêtre et lance la simulation, protégé en cas d'erreur."""
        try:
            starting_time = time()
            self.start_loop(duration)
            real_duration = time() - starting_time
            simulation_speed = round(duration/real_duration, 2)
            print(f"Simulation {tbold(self.title)} terminée au bout de {real_duration}s{(', soit ' + str(simulation_speed) + ' fois la durée réelle') if simulation_speed < INF else ''}.")
        except Exception as exception:
            self.print_errors(exception)
        finally:
            self.print_simulation_info()

    def print_simulation_info(self):
        """Affiche l'ensemble des objects et leurs principaux attributs dans la sortie standard."""
        if s.SHOW_DETAILED_LOGS:
            print(f"\n{tbold('--- Simulation Infos ---')}\n\n{self.size = }\n{self.t = }\n{self.FPS = }\n{self.dt = }\n{self.speed = }\n{self.speed_ajusted_fps = }\n{self.paused = }\n{self.over = }\n{self.dragging = }\n{self.off_set = }\n{self.road_graph = }\n")
            for road in self.roads:
                print(f"\n{road} :\n    TrafficLight : {road.traffic_light}\n    Cars :")
                for car in road.cars:
                    print(f"        {car}")
                print("    Sensors :")
                for sensor in road.sensors:
                    print(f"        {sensor}")
                print(f"    CarFactory : {road.car_factory}\n    CarSorter : {road.car_sorter}\n")

    @staticmethod
    def print_errors(exception):
        """Affiche la dernière erreur dans la sortie standard."""
        if s.SHOW_ERRORS:
            print(tred(f"\n*** Erreur : {exception} ***\n\n{traceback.format_exc()}"))

    def show_info(self, info: str):
        """Affiche des informations en haut à gauche de la fenêtre et l'échelle si besoin."""
        text_width, text_height = self.FONT.size(info)
        draw_rect(self.surface, s.INFO_BACKGROUND_COLOR, npz(2), text_width + 30, text_height + 20)
        draw_text(self.surface, s.FONT_COLOR, npa((10, 10)), info, self.FONT)

        if s.SHOW_SCALE:
            self.show_scale()

    def show_scale(self):
        """Affiche l'échelle en bas à gauche de la fenêtre."""
        _, h = self.size
        n = 10
        x, y = 30, h - 40
        text = f"{n * s.SCALE}px = {n}m"
        tw, th = self.FONT.size(text)
        draw_rect(self.surface, BLACK, npa((x, y)), n * s.SCALE, 10)  # affiche la barre de n*SCALE pixels
        for i in range(1, n, 2):  # affiche les graduations
            draw_rect(self.surface, self.bg_color, npa((x + i*s.SCALE, y + 1)), s.SCALE - 2/n, 8)
        draw_text(self.surface, BLACK, npa((x + (n * s.SCALE - tw) / 2, y - th - 2)), text, self.SMALL_FONT)  # affiche la description

    @property
    def info_to_show(self):
        """Renvoie les informations à afficher sur la fenêtre : horloge, vitesse..."""
        str_speed = self.speed if self.speed != int(self.speed) else int(self.speed)
        duration_perc = f" = {int(self.t/self.duration*100):>2}%" if self.duration < INF else ""
        return f"t = {round(self.t, 2):<7} = {round(self.t//60):>02}m{round(self.t) % 60:02}s{duration_perc} | vitesse = ×{str_speed:<4} | {'en pause' if self.paused else 'en cours'}"

    def manage_event(self, event):
        """Gère les conséquences en cas d'un certain évenement pygame, c'est-à-dire une action de l'utilisateur (pause, changement de vitesse, déplacement...)."""
        if event.type == pygame.QUIT:  # arrêter la boucle quand la fenêtre est fermée
            self.over = True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # quitte quand on appuie sur escape
                self.over = True
            elif event.key == pygame.K_SPACE:
                # met la simulation en pause quand on appuie sur espace
                self.paused = not self.paused
                if self.paused:  # si on passe de en cours à en pause, afficher les infos
                    self.print_simulation_info()
                    if s.SENSOR_PRINT_RES_AT_PAUSE:
                        self.print_sensors_results()
                    if s.SENSOR_EXPORT_RES_AT_PAUSE:
                        self.export_sensors_results()
            elif event.key in (pygame.K_LEFT, pygame.K_DOWN) and self.speed >= 0.5:
                # si l'utilisateur appuie sur la flèche gauche ou bas, ralentir jusqu'à 0.25
                self.speed = round(self.speed / 2, 2)
                self.speed_ajusted_fps = round(self.speed_ajusted_fps / 2, 2)
            elif event.key in (pygame.K_RIGHT, pygame.K_UP) and 2 * self.speed <= s.MAX_SPEED:
                # si l'utilisateur appuie sur la flèche droite ou haut, accélérer jusqu'à 32
                self.speed = round(self.speed * 2, 2)
                self.speed_ajusted_fps = round(self.speed_ajusted_fps * 2, 2)
            elif event.key == pygame.K_RETURN:
                # si l'utilisateur appuie sur entrer, recentrer la fenêtre
                self.off_set = (0, 0)

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

    def show_car(self, car: Car):
        """Affiche une voiture."""
        if s.CAR_SHOW_BUMPING_BOXES:  # si on affiche les zones de collision
            r, g, b = car.color
            brighten = lambda color: min(int(color * 1.3), 255)
            side_bumper_color = (brighten(r*1.2), brighten(g), brighten(b))  # même couleur plus claire et plus rouge
            front_bumper_color = (brighten(r), brighten(g*1.2), brighten(b))  # même couleur plus claire et plus verte
            draw_polygon(self.surface, side_bumper_color, car.side_bumper_hurtbox, self.off_set)
            draw_polygon(self.surface, front_bumper_color, car.front_bumper_hitbox, self.off_set)

        if s.CAR_SPEED_CODED_COLOR:  # si la couleur de la voiture dépend de sa vitesse
            car_color = blue_red_gradient(car.v/(s.V_MAX*s.SCALE))
        else:
            car_color = car.color

        draw_polygon(self.surface, car_color, car.corners, self.off_set)  # affiche le rectangle qui représente la voiture

        if s.CAR_SHOW_ARROW:  # si on affiche la direction de la voiture
            rotated_arrow = pygame.transform.rotate(self.CAR_ARROW, car.road.angle)
            draw_image(self.surface, rotated_arrow, car.road.dist_to_pos(car.d), self.off_set)

        elif s.CAR_SHOW_SPEED_MS or s.CAR_SHOW_SPEED_KMH:  # si on affiche la vitesse de la voiture
            coeff = 3.6 if s.CAR_SHOW_SPEED_KMH else 1
            text = str(round(coeff * car.v / s.SCALE))
            text_width, text_height = self.SMALL_FONT.size(text)
            x = car.pos[0] - text_width / 2
            y = car.pos[1] - text_height / 2
            draw_text(self.surface, s.FONT_COLOR, npa((x, y)), text, self.SMALL_FONT, off_set=self.off_set)

        elif s.CAR_SHOW_ID:  # si on affiche l'id de la voiture
            text = str(car.id)
            text_width, text_height = self.SMALL_FONT.size(text)
            x = car.pos[0] - text_width / 2
            y = car.pos[1] - text_height / 2
            draw_text(self.surface, s.FONT_COLOR, npa((x, y)), text, self.SMALL_FONT, off_set=self.off_set)

    def show_roads(self, road_list: Sequence[Road | ArcRoad]):
        """Affiche des routes."""
        for road in road_list:
            if isinstance(road, Road):
                draw_polygon(self.surface, road.color, road.coins, self.off_set)

                rotated_arrow = pygame.transform.rotate(self.ROAD_ARROW, road.angle)

                for arrow_coord in road.arrows_coords:
                    x, y, _ = arrow_coord
                    draw_image(self.surface, rotated_arrow, npa((x, y)), self.off_set)
            elif isinstance(road, ArcRoad):
                self.show_roads(road.sroads)

    def show_traffic_light(self, traffic_light: TrafficLight):
        """Affiche les feux de signalisations."""
        if traffic_light is not None and not traffic_light.static:
            color = {0: s.TL_RED, 1: s.TL_ORANGE, 2: s.TL_GREEN}[traffic_light.state]
            draw_polygon(self.surface, color, traffic_light.coins, self.off_set)

    def show_sensor(self, sensor: Sensor):
        draw_polygon(self.surface, s.SENSOR_COLOR, sensor.corners, self.off_set)

    def print_sensor_results(self, sensor: Sensor):
        if sensor.results.strip():
            text = tbold(f"À t={round(self.t, 2)}s, {sensor} sur Road(id={sensor.road.id}) :\n") + sensor.results + "\n"
            print(text)

    def print_sensors_results(self, *sensors_id):
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    self.print_sensor_results(sensor)
        else:
            for sensor_id in sensors_id:
                sensor = get_by_id(sensor_id)
                self.print_sensor_results(sensor)

    def export_sensor_results(self, sensor: Sensor, describe: bool):
        file_name = f"{self.title}_capteur{sensor.id}_{strftime('%H%M%S_%d%m%y')}.xlsx"
        sheet_name = f"{self.title} ({round(self.t, 2)}s) capteur {sensor.id}"
        sensor.export(file_path=s.SENSOR_EXPORTS_DIRECTORY + file_name, sheet_name=sheet_name, describe=describe)

    def export_sensors_results(self, *sensors_id, describe: bool = True):
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    self.export_sensor_results(sensor, describe)
        else:
            for sensor_id in sensors_id:
                sensor = get_by_id(sensor_id)
                self.export_sensor_results(sensor, describe)

    def plot_sensors_results(self, *sensors_id):
        if not sensors_id:
            for road in self.roads:
                for sensor in road.sensors:
                    sensor.plot()
        else:
            for sensor_id in sensors_id:
                if isinstance(sensor_id, int):
                    get_by_id(sensor_id).plot()
                else:
                    s_id, x = sensor_id
                    get_by_id(s_id).plot(x)

        plt.show()

    def create_road(self, **kw):
        """Créer une route."""
        start, end, vdstart, vdend, v_max, car_factory, color, w, obj_id = kw.get("start", (0, 0)), kw.get("end", (0, 0)), kw.get("vdstart"), kw.get("vdend"), kw.get("v_max", s.V_MAX), kw.get("car_factory"), kw.get("color", s.ROAD_COLOR), kw.get("width", s.ROAD_WIDTH), kw.get("id")
        start, end, vdstart, vdend = self.rc_to_sc(start), self.rc_to_sc(end), self.rc_to_sc(vdstart), self.rc_to_sc(vdend)
        v_max *= s.SCALE  # mise à l'échelle de v_max
        if isinstance(start, int):  # si l'argument start est un id de route
            rstart = get_by_id(start)
            start = rstart.end
            vdstart = rstart.vd
        if isinstance(end, int):  # si l'argument end est un id de route
            rend = get_by_id(end)
            end = rend.start
            vdend = rend.vd
        if kw["type"] == "road":  # si on crée une route droite
            traffic_light, wa, sensors = kw.get("traffic_light"), kw.get("with_arrows", True), kw.get("sensors")
            road = Road(start=start, end=end, width=w, color=color, v_max=v_max, with_arrows=wa, car_factory=car_factory, traffic_light=traffic_light, sensors=sensors, obj_id=obj_id)
        else:  # si on crée une route courbée
            n = kw.get("n", s.ARCROAD_NUM_OF_SROAD)
            road = ArcRoad(start=start, end=end, vdstart=vdstart, vdend=vdend, n=n, v_max=v_max, width=w, color=color, car_factory=car_factory, obj_id=obj_id)
        self.roads.append(road)
        self.road_graph[road.id] = None
        return road

    def create_roads(self, road_list: list[dict]):
        """Créer des routes, renvoie la liste des routes.

        Les éléments de ``road_list`` sont des dictionnaires de la forme :\n
        - pour une route droite, ``{"id": int (optionnel), "type": "road", "start": (float, float) | int, "end": (float, float) | int, "v_max": float (optionnel), "car_factory": CarFactory (optionnel), "traffic_light": TrafficLight (optionnel), "with_arrows": bool (optionnel)}``
        - pour une route courbée, ``{"id": int (optionnel), "type": "arcroad", "start": (float, float) | int, "vdstart": (float, float), "end": (float, float) | int, "vdend": (float, float), "v_max": float (optionnel), "n": int (optionnel), "car_factory": CarFactory (optionnel)}``

        avec :\n
        - ``id`` l'éventuel l'identifiant de la route
        - ``start`` les coordonnées du début de la route (éventuellement négatives), ou l'identifiant d'une route déjà définie dont la fin servira de début
        - ``end`` les coordonnées de la fin de la route (éventuellement négatives), ou l'identifiant d'une route déjà définie dont le début servira de fin
        - ``v_max`` l'éventuelle limite de vitesse (en m/s) de la route, par défaut ``V_MAX``
        - ``car_factory`` l'éventuel CarFactory
        - ``vdstart`` pour arcroad, si ``start`` est un couple de coordonnées, vecteur directeur du début
        - ``vdend`` pour arcroad, si ``end`` est un couple de coordonnées, vecteur directeur de la fin
        - ``n`` pour arcroad, l'éventuel nombre de routes droites la composant, par défaut ``N_ARCROAD``
        - ``traffic_light`` pour road, l'éventuel TrafficLight
        - ``with_arrow`` pour road, si des flèches seront affichées sur la route dans le sens de la circulation
        """
        return [self.create_road(**road) for road in road_list]

    def set_road_graph(self, graph: dict):
        """Définie le graphe des routes de la simulation.

        :param graph: graphe des routes, de type ``{road_id1: road_id2, road_id3: {road_id1: proba1, road_id4: propa4}}``"""
        self.road_graph = graph
        for road in self.roads:
            next_roads = graph[road.id]
            if isinstance(next_roads, int):
                car_sorter = CarSorter(method={next_roads: 1})
            else:
                car_sorter = CarSorter(method=next_roads)

            road.car_sorter = car_sorter

    def get_leaders(self, road: Road, avg: bool):
        """
        Renvoie les éventuels leaders de la première voiture de la route, dans une liste de la forme ``[(car, distance, importance), ...]``.

        :param road: route en question
        :param avg: méthode de recherche : si True, renvoie les dernières voitures des prochaines routes, coefficientées par la probabilité que la première voiture aille sur ces routes. Sinon, renvoie celles de la dernière voiture de la prochaine route de la première voiture de la route.
        """
        if avg:  # si GET_LEADER_COORDS_METHOD_AVG est True
            next_roads_probs = self.road_graph[road.id]  # récupération des prochaines routes et de leurs probas

            if next_roads_probs is None:  # si pas de prochaine route
                return []

            if isinstance(next_roads_probs, int):  # si un seul choix de prochaine route
                next_roads_probs = {next_roads_probs: 1}

            leaders = []

            for next_road_id in next_roads_probs:  # pour chaque prochaine route
                prob = next_roads_probs[next_road_id]  # on récupère la probabilité
                next_road = get_by_id(next_road_id)

                if next_road.cars:  # si elle contient des voitures, on prend les coordonnées de la première
                    next_car = next_road.cars[-1]
                    leaders.append((next_car, next_car.d, prob * s.CAR_LEADERS_COEFF_NEXT_ROAD_CAR))
                else:  # sinon, on cherche plus loin
                    next_leaders = self.get_leaders(next_road, avg=True)
                    leaders += [(next_car, next_road.length + d, prob * next_prob) for next_car, d, next_prob in next_leaders]

            return leaders

        else:  # si GET_LEADER_COORDS_METHOD_AVG est False

            next_road = road.cars[0].next_road

            if next_road is None:  # dans le rare cas où la première voiture n'a pas encore de prochaine route
                return self.get_leaders(road, avg=True)
            elif next_road.cars:  # si elle en a une et qu'elle contient des voitures
                next_car = next_road.cars[-1]
                return [(next_car, next_car.d, s.CAR_LEADERS_COEFF_NEXT_ROAD_CAR)]
            else:  # si elle en a une mais qui ne contient pas de voiture
                next_leaders = self.get_leaders(next_road, avg=True)
                return [(next_car, next_road.d + d, next_prob) for next_car, d, next_prob in next_leaders]

    def get_bumping_cars(self, car: Car):
        """Renvoie les voitures avec lequelles ``car`` rentre en collision."""
        if not s.USE_BUMPING_BOXES or not is_inside_circle(car.pos, self.bumping_zone):
            return []

        else:
            bumping_cars = []

            for road in self.roads:
                if road != car.road:
                    for other_car in road.cars:
                        is_bumping = car.is_bumping_with(other_car)
                        is_bumping_first = car not in [leader for leader, _, _ in other_car.leaders]
                        if is_bumping and is_bumping_first and other_car != car:
                            d = length(car.pos, other_car.pos)
                            bumping_cars.append((other_car, d, s.CAR_LEADERS_COEFF_BUMPING_CARS))

            return bumping_cars

    def def_bumping_zone(self, center: tuple[float, float] = None, radius: float = INF):
        """
        Définie la zone circulaire où la simulation utilise les hitbox et hurtbox des voitures pour éviter les collisions.
        La détection de collision sera automatiquement activée, même si ``USE_BUMPING_BOXES = False``.

        :param center: centre du disque décrivant la zone, centre de la fenêtre par défaut
        :param radius: rayon du disque décrivant la zone, +inf par défaut
        """
        s.USE_BUMPING_BOXES = True

        if center is None:
            center = self.size/2

        self.bumping_zone = (npa(self.rc_to_sc(center)), radius)

    def show_bumping_zone(self):
        center, radius = self.bumping_zone
        if s.SHOW_BUMPING_ZONE and radius < INF:
            da = lambda color: int(color * 0.93)
            r, g, b = self.bg_color
            draw_circle(self.surface, (da(r), da(g), da(b)), center, radius, self.off_set)
