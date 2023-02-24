from time import time, strftime
import pygame.event
from matplotlib import pyplot as plt

from .components import *
from .drawing import *
from .constants import *


class Simulation:
    def __init__(self, title: str = "Traffic Simulation", width: Optional[int] = None, height: Optional[int] = None):
        """
        Simulation du trafic.

        :param title: titre de la fenêtre
        :param width: largeur de la fenêtre, en pixels. Détectée automatiquement si non fourni, puis récupérable avec Simulation.size[0].
        :param height: hauteur de la fenêtre, en pixels. Détectée automatiquement si non fourni, puis récupérable avec Simulation.size[1].
        """
        self.id = 0
        ids[0] = self
        self.title = title  # titre de la fenêtre
        pygame.init()  # initialisation de pygame
        pygame.display.set_caption(title)  # modification du titre de la fenêtre
        monitor_info = pygame.display.Info()
        if width is None:
            width = monitor_info.current_w
        if height is None:
            height = monitor_info.current_h
        self.size = width, height  # taille de la fenêtre
        self.t = 0.0  # suivi du temps
        self.FPS = s.FPS  # images par seconde
        self.dt = 1 / s.FPS  # pas de temps
        self.speed_ajusted_fps = s.FPS * s.SPEED  # FPS ajusté pour la vitesse de la simulation
        self.speed = s.SPEED  # vitesse de la simulation
        self.over = self.paused = False  # si la simulation est finie ou en pause
        self.duration = INF  # durée de la simulation, définie dans self.start_loop() par l'utilisateur

        self.roads = []  # liste des routes
        self.road_graph = {}  # graphe des routes
        self.bumping_zone = (npz(2), INF)  # zone où get_bumping_cars est utilisé

        self.surface = pygame.display.set_mode(self.size)  # création de la fenêtre
        self.clock = pygame.time.Clock()  # création de l'horloge pygame
        self.bg_color = s.BACKGROUND_COLOR  # couleur d'arrière-plan de la fenêtre
        self.surface.fill(self.bg_color)  # coloriage de l'arrière-plan

        self.FONT = pygame.font.Font(s.FONT_PATH, s.FONT_SIZE)  # police d'écriture des informations
        self.SMALL_FONT = pygame.font.Font(s.FONT_PATH, round(s.CAR_WIDTH * s.SCALE * 0.8))  # pour les voitures
        arrow = pygame.image.load(s.ARROW_PATH).convert_alpha()  # chargement de l'image de flèche
        self.ARROW = pygame.transform.smoothscale(arrow, (s.ROAD_WIDTH * s.SCALE * 0.7, s.ROAD_WIDTH * s.SCALE * 0.7))  # ajustement de la taille des flèches pour les routes
        self.road_rotated_arrows = {}  # générer l'image de flèche avec l'angle de la route est très long, on le fera qu'une fois au début pour la garder
        self.SMALL_ARROW = pygame.transform.smoothscale(arrow, (s.CAR_WIDTH * 0.8, s.CAR_WIDTH * 0.8))  # pour les voitures
        self.road_small_rotated_arrows = {}  # idem

        self.off_set = npz(2)  # décalage par rapport à l'origine, pour bouger la simulation
        self.dragging = False  # si l'utilisateur est en train de bouger la simulation
        self.mouse_last = npz(2)  # dernières coordonnées de la souris

    def rc_to_sc(self, coordinates: Vecteur | None, is_vect: bool = False):
        """Convertie des coordonnées naturelles (abscisses vers la droite, ordonnées vers le haut) en coordonnées
        de la simulation (abscisses vers la droite, ordonnées vers le bas)."""
        if isinstance(coordinates, (float, int, type(None))):
            return coordinates

        x, y = coordinates
        _, h = self.size if not is_vect else (0, 0)
        return npa([x, h - y])

    def start_loop(self, duration: float):
        """Lance la boucle de la simulation, en actualisant chaque élément et en les affichant ``FPS`` fois par
        seconde, pendant une durée ``duration``."""
        self.duration = duration

        # initialisation des images flèches orientées dans le sens des routes
        for road in self.roads:
            if isinstance(road, Road):
                if road.with_arrows:
                    self.road_rotated_arrows[road.id] = pygame.transform.rotate(self.ARROW, road.angle)
                    self.road_small_rotated_arrows[road.id] = pygame.transform.rotate(self.SMALL_ARROW, road.angle)
            elif isinstance(road, ArcRoad):
                for sroad in road.sroads:
                    if sroad.with_arrows:
                        self.road_rotated_arrows[sroad.id] = pygame.transform.rotate(self.ARROW, sroad.angle)
                        self.road_small_rotated_arrows[sroad.id] = pygame.transform.rotate(self.SMALL_ARROW, sroad.angle)

        while not self.over:  # tant que la simulation n'est pas terminée
            for event in pygame.event.get():  # on regarde les dernières actions de l'utilisateur
                self.manage_event(event)

            self.surface.fill(self.bg_color)  # efface tout

            self.show_bumping_zone()  # affiche la zone où les collisions sont détectées
            self.show_roads(self.roads)  # affiche les routes

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

            # on actualise la simulation route par route
            for road in self.roads:
                # affichage des voitures de la route et mise à jour des prévisions de collision
                for car in road.cars:
                    self.show_car(car)
                    self.update_bumping_cars(car)

                # affichage des capteurs de la route
                for sensor in road.sensors:
                    self.show_sensor(sensor)

                # affichage de l'élément de signalisation (feu/panneau stop) de la route
                self.show_sign(road.sign)

                # actualisation des coordonnées des voitures de la route, des capteurs et du panneau
                road_leaders = self.get_road_leaders(road, avg=s.GET_LEADERS_METHOD_AVG)
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

    def start(self, duration: float = INF):
        """Ouvre une fenêtre et lance la simulation."""
        if duration <= 0:
            raise ValueError("La simulation doit avoir une durée strictement positive !")

        if not self.roads:
            raise NotImplementedError("Aucune route n'a été définie. Vous pouvez définir des routes avec create_roads().")

        try:
            starting_time = time()
            self.start_loop(duration)
            real_duration = time() - starting_time
            if duration == INF:
                duration = self.t
            simulation_speed = real_duration / duration
            print(f"Simulation {tbold(self.title)} terminée au bout de {duration:.4f}s ({real_duration:.4f}s), soit {simulation_speed:.4f}× la durée réelle.\n")
        except Exception as exception:
            print_errors(exception)
        finally:
            self.print_simulation_info()

    def print_simulation_info(self):
        """Affiche l'ensemble des objects et leurs principaux attributs dans la sortie standard."""
        if s.PRINT_DETAILED_LOGS:
            print(f"\n{tbold('--- Simulation Infos ---')}\n\n{self.size = }\n{self.t = }\n{self.FPS = }\n{self.dt = }\n{self.speed = }\n{self.speed_ajusted_fps = }\n{self.paused = }\n{self.over = }\n{self.dragging = }\n{self.off_set = }\n{self.road_graph = }\n")
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
                    if s.SENSOR_PRINT_RES_AT_PAUSE:
                        self.print_sensors_results()
                    if s.SENSOR_EXPORT_RES_AT_PAUSE:
                        self.export_sensors_results()
            elif event.key in (pygame.K_LEFT, pygame.K_DOWN) and self.speed >= 0.5:
                # si l'utilisateur appuie sur la flèche gauche ou bas
                self.speed = round(self.speed / 2, 2)
                self.speed_ajusted_fps = round(self.speed_ajusted_fps / 2, 2)
            elif event.key in (pygame.K_RIGHT, pygame.K_UP) and 2 * self.speed <= s.MAX_SPEED:
                # si l'utilisateur appuie sur la flèche droite ou haut, accélérer jusqu'à MAX_SPEED
                self.speed = round(self.speed * 2, 2)
                self.speed_ajusted_fps = round(self.speed_ajusted_fps * 2, 2)
            elif event.key == pygame.K_RETURN:
                # si l'utilisateur appuie sur entrer, recentrer la fenêtre
                self.off_set = (0, 0)
            elif event.key == pygame.K_s:
                # si l'utilisateur appuie sur S, enregistrer la fenêtre
                filename = f"screenshot_{self.title}_{self.t}.jpg"
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

    def show_info(self, info: str):
        """Affiche des informations en haut à gauche de la fenêtre et l'échelle si besoin."""
        if s.SHOW_INFOS:
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
            draw_rect(self.surface, self.bg_color, npa((x + i * s.SCALE, y + 1)), s.SCALE - 2 / n, 8)
        draw_text(self.surface, BLACK, npa((x + (n * s.SCALE - tw) / 2, y - th - 2)), text, self.FONT)  # affiche la description

    def show_car(self, car: Car):
        """Affiche une voiture."""
        if s.CAR_SHOW_BUMPING_BOXES:  # si on affiche les zones de collision
            r, g, b = car.color
            alpha = 1.2 if is_inside_circle(car.pos, self.bumping_zone) else 0.9
            f = lambda color: min(int(color * alpha), 255)
            side_bumper_color = (f(r * 1.2), f(g), f(b))  # même couleur plus claire et plus rouge
            front_bumper_color = (f(r), f(g * 1.2), f(b))  # même couleur plus claire et plus verte
            draw_polygon(self.surface, side_bumper_color, car.side_bumper_hurtbox, self.off_set)
            draw_polygon(self.surface, front_bumper_color, car.front_bumper_hitbox, self.off_set)

        if s.CAR_SHOW_LEADER_LINKS:
            if car.bumping_cars:
                for leader in car.bumping_cars:
                    draw_line(self.surface, car.color, car.pos, leader.pos, self.off_set)
            else:
                for leader, _ in car.leaders:
                    draw_line(self.surface, car.color, car.pos, leader.pos, self.off_set)

        if s.CAR_SPEED_CODED_COLOR:  # si la couleur de la voiture dépend de sa vitesse
            car_color = blue_red_gradient(car.v / (s.V_MAX * s.SCALE))
        else:
            car_color = car.color

        draw_polygon(self.surface, car_color, car.vertices,
                     self.off_set)  # affiche le rectangle qui représente la voiture

        if s.CAR_SHOW_ARROW:  # si on affiche la direction de la voiture
            rotated_arrow = self.road_small_rotated_arrows[car.road.id]
            draw_image(self.surface, rotated_arrow, car.road.dist_to_pos(car.d), self.off_set)

        roof_text = ""

        if s.CAR_SHOW_SPEED_MS:  # si on affiche la vitesse de la voiture en m/s
            text = str(round(car.v / s.SCALE))
            roof_text += text
        if s.CAR_SHOW_SPEED_KMH:  # si on affiche la vitesse en km/h
            text = str(round(3.6 * car.v / s.SCALE))
            roof_text += ("|" if roof_text else "") + text
        if s.CAR_SHOW_ID:  # si on affiche l'id de la voiture
            text = str(car.id)
            roof_text += ("|" if roof_text else "") + text
        if roof_text:
            text_width, text_height = self.SMALL_FONT.size(roof_text)
            x = car.pos[0] - text_width / 2
            y = car.pos[1] - text_height / 2
            draw_text(self.surface, s.FONT_COLOR, npa((x, y)), roof_text, self.SMALL_FONT, off_set=self.off_set)

    def show_roads(self, road_list: Sequence[Road | ArcRoad]):
        """Affiche des routes."""
        for road in road_list:
            if isinstance(road, Road):
                draw_polygon(self.surface, road.color, road.vertices, self.off_set)

                rotated_arrow = self.road_rotated_arrows[road.id]

                for arrow_coord in road.arrows_coords:
                    x, y, _ = arrow_coord
                    draw_image(self.surface, rotated_arrow, npa((x, y)), self.off_set)
            elif isinstance(road, ArcRoad):
                self.show_roads(road.sroads)

    def show_sign(self, sign: TrafficLight | StopSign):
        """Affiche un élément de signalisation."""
        if isinstance(sign, TrafficLight) and not sign.static:
            color = {0: s.TL_RED, 1: s.TL_ORANGE, 2: s.TL_GREEN}[sign.state]
            draw_polygon(self.surface, color, sign.vertices, self.off_set)
        elif isinstance(sign, StopSign):
            draw_polygon(self.surface, s.SS_COLOR, sign.vertices, self.off_set)

    def show_sensor(self, sensor: Sensor):
        """Affiche un capteur."""
        draw_polygon(self.surface, s.SENSOR_COLOR, sensor.vertices, self.off_set)

    def show_bumping_zone(self):
        """Affiche la zone où les collisions sont gérées."""
        center, radius = self.bumping_zone
        if s.SHOW_BUMPING_ZONE and radius < INF:
            da = lambda color: int(color * 0.93)
            r, g, b = self.bg_color
            draw_circle(self.surface, (da(r), da(g), da(b)), center, radius, self.off_set)

    def print_sensor_results(self, sensor: Sensor):
        """Affiche les résultats d'un capteur dans la sortie standard."""
        if sensor.results.strip():
            text = tbold(f"Résulats à t={round(self.t, 2)}s de {sensor} sur Road(id={sensor.road.id}) :\n") + sensor.results + "\n"
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
        file_name = f"{self.title}_capteur{sensor.id}_{strftime('%H%M%S_%d%m%y')}.xlsx"
        sheet_name = f"{self.title} ({round(self.t, 2)}s) capteur {sensor.id}"
        sensor.export(file_path=s.SENSOR_EXPORTS_DIRECTORY + file_name, sheet_name=sheet_name, describe=describe)

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

    def plot_sensors_results(self, *sensors_id):
        """Affiche les résulats de capteurs sous forme d'un graphe de fonctions."""
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
        """Créer une route, renvoie la route."""
        # récupération des paramètres communs à tous les types de route
        start = kw.get("start", kw.get("s", (0, 0)))  # start ou son alias s, par défaut (0, 0)
        end = kw.get("end", kw.get("e", self.size))  # end ou son alias e, par défaut (height, width) de la fenêtre
        v_max = kw.get("v_max", s.V_MAX)  # v_max, par défaut s.V_MAX
        car_factory = kw.get("car_factory", kw.get("cf"))  # car_factory ou son alias cf, par défaut None
        color = kw.get("color", kw.get("c", s.ROAD_COLOR))  # color ou son alias c, par défaut s.ROAD_COLOR
        width = kw.get("width", kw.get("w", s.ROAD_WIDTH))  # width ou son alias w, par défaut s.WIDTH
        obj_id = kw.get("id")  # id, par défaut None

        # conversion des coordonnées classiques en coordonnées pygame (ne change pas les int ou float)
        start, end = self.rc_to_sc(start), self.rc_to_sc(end)

        # mises à l'échelle
        v_max *= s.SCALE
        width *= s.SCALE

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

        if kw.get("type", "road") in ["road", "r"]:  # si on crée une route droite
            sign, with_arrows, sensors = kw.get("sign"), kw.get("with_arrows", True), kw.get("sensors")
            road = Road(start=start, end=end, width=width, color=color, v_max=v_max, with_arrows=with_arrows,
                        car_factory=car_factory, sign=sign, sensors=sensors, obj_id=obj_id)

        elif kw["type"] in ["arcroad", "arc", "a"]:  # si on crée une route courbée
            n = kw.get("n", s.ARCROAD_NUM_OF_SROAD)
            road = ArcRoad(start=start, end=end, vdstart=npa(vdstart), vdend=npa(vdend), n=n, v_max=v_max, width=width,
                           color=color, car_factory=car_factory, obj_id=obj_id)
        else:
            raise ValueError(f'Le type de route doit être parmi "", "road", "r", "arcroad", "arc" ou "a", pas "{kw["type"]}".')

        self.roads.append(road)

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
        """
        Définie le graphe des routes de la simulation. Prend en argument le graphe des routes, qui est un dictionnaire
        qui à l'identifiant d'une route associe une des choses suivantes :

        - l'identifiant d'une autre route
        - un dictionnaire associant l'identifiant d'une autre route à la probabilité d'aller sur cette route
        - une fonction f(t: float) -> int qui au temps **d'arrivée** de la voiture sur la route associe l'identifiant d'une autre route
        - None ou {} pour supprimer les voitures qui sortent de la route (ne pas inclure l'identifiant de la route dans le dictionnaire a le même effet)

        :param graph: graphe des routes
        """
        self.road_graph = graph  # on enregistre le graphe

        for road in self.roads:
            road.car_sorter = CarSorter(graph.get(road.id))

            if road.car_sorter.method == "user func":
                self.road_graph[road.id] = None

            if isinstance(road, ArcRoad):
                for i in range(road.n - 1):
                    self.road_graph[road.sroads[i].id] = road.sroads[i + 1].id
                self.road_graph[road.sroads[-1].id] = self.road_graph.get(road.id)

    def get_road_leaders(self, road: Road, avg: bool, rec_depth: int = 0):
        """
        Renvoie les éventuels leaders de la première voiture de la route, dans une liste de la forme ``[(car, distance, importance), ...]``, par un parcours en profondeur.

        :param road: route en question
        :param avg: méthode de recherche : si True, renvoie les dernières voitures des prochaines routes, pondérées par la probabilité que la première voiture aille sur ces routes. Sinon, renvoie celles de la dernière voiture de la prochaine route de la première voiture de la route.
        :param rec_depth: niveau de récursion atteint
        """
        if rec_depth > s.GET_LEADERS_MAX_REC_DEPTH:
            return []

        if avg:
            next_roads_probs = self.road_graph.get(road.id)  # récupération des prochaines routes et de leurs probabilités

            if next_roads_probs is None:  # si pas de prochaine route
                return []

            if isinstance(next_roads_probs, int):  # si un seul choix de prochaine route
                next_roads_probs = {next_roads_probs: 1}

            leaders = []

            for next_road_id in next_roads_probs:  # pour chaque prochaine route
                next_road = get_by_id(next_road_id)

                if isinstance(next_road, ArcRoad):
                    next_road = next_road.sroads[0]

                if next_road.cars:  # si elle contient des voitures, on prend les coordonnées de la première
                    next_car = next_road.cars[-1]
                    leaders.append((next_car, next_car.d - next_car.length / 2))
                elif next_road.sign.dummy_car is not None:  # si elle a un élément de signalisation actif, on le prend lui
                    leaders.append((next_road.sign.dummy_car, next_road.length))
                else:  # sinon, on cherche plus loin
                    next_leaders = self.get_road_leaders(next_road, avg=True, rec_depth=rec_depth + 1)
                    leaders += [(next_car, next_road.length + d) for next_car, d in next_leaders]

        else:

            if not road.cars:
                return []

            next_road = road.cars[0].next_road

            if isinstance(next_road, ArcRoad):
                next_road = next_road.sroads[0]

            if next_road is None:  # dans le cas où la première voiture n'a pas encore de prochaine route
                leaders = self.get_road_leaders(road, avg=True, rec_depth=rec_depth + 1)
            elif next_road.cars:  # si elle en a une et qu'elle contient des voitures
                next_car = next_road.cars[-1]
                leaders = [(next_car, next_car.d)]
            elif next_road.sign.dummy_car is not None:  # si elle a un élément de signalisation actif
                leaders = [(next_road.sign.dummy_car, next_road.length)]
            else:  # si elle en a une mais qui ne contient pas de voiture
                next_leaders = self.get_road_leaders(next_road, avg=True, rec_depth=rec_depth + 1)
                leaders = [(next_car, next_road.length + d) for next_car, d in next_leaders]

        return leaders

    def update_bumping_cars(self, car: Car):
        """Met à jour les voitures avec lesquelles ``car`` rentre en collision."""
        if not s.USE_BUMPING_BOXES or not is_inside_circle(car.pos, self.bumping_zone):
            return

        else:
            for road in self.roads:
                for other_car in road.cars:
                    # les conditions sont dans l'ordre croissant en coût de calcul
                    if other_car != car:
                        if car not in other_car.bumping_cars:
                            if is_inside_circle(other_car.pos, self.bumping_zone):
                                if car.is_bumping_with(other_car):
                                    car.bumping_cars.append(other_car)

    def set_bumping_zone(self, center: tuple[float, float] | Vecteur = None, radius: float = INF):
        """
        Définie la zone circulaire où la simulation utilise les hitbox et hurtbox des voitures pour éviter les collisions.
        La détection de collision sera automatiquement activée, même si ``USE_BUMPING_BOXES = False``.

        :param center: centre du disque décrivant la zone, centre de la fenêtre par défaut
        :param radius: rayon du disque décrivant la zone, en **pixels**, +inf par défaut
        """
        s.USE_BUMPING_BOXES = True

        if center is None:
            center = self.size[0] / 2, self.size[1] / 2

        self.bumping_zone = (npa(self.rc_to_sc(center)), radius)
