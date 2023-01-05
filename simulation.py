from objets import *
from drawing import *
import settings as s
import pygame
import traceback


class Simulation:
    def __init__(self, win_title="Traffic Simulation", width=1440, height=820):
        """
        Simulation du traffic.

        :param win_title: titre de la fenêtre
        :param width: targeur de la fenêtre, en pixels
        :param height: hauteur de la fenêtre, en pixels
        """
        self.id = new_id(self, 0)
        self.size = width, height  # taille de la fenêtre
        self.t = 0.0  # suivi du temps
        self.FPS = s.FPS  # images par seconde
        self.dt = 1/self.FPS  # pas de temps
        self.speed_ajusted_dt = self.dt * s.SPEED  # pas de temps ajusté pour la vitesse de la simulation
        self.speed = float(s.SPEED)  # vitesse de la simulation
        self.over = self.paused = False  # si la simulation est finie ou en pause

        self.roads = []  # liste des routes
        self.road_graph = {}  # graphe des routes

        pygame.init()  # initialisation de pygame
        pygame.display.set_caption(win_title)  # modification du titre de la fenêtre

        self.surface = pygame.display.set_mode(self.size)  # création de la fenêtre
        self.clock = pygame.time.Clock()  # création de l'horloge pygame
        self.bg_color = s.BG_COLOR  # couleur d'arrière plan de la fenêtre
        self.surface.fill(self.bg_color)  # coloriage de l'arrière plan
        self.FONT = pygame.font.Font(s.FONT_PATH, s.FONT_SIZE)  # police d'écriture des informations
        self.CAR_FONT = pygame.font.Font(s.FONT_PATH, round(s.CAR_WIDTH*0.8))  # pour les voitures

        arrow = pygame.image.load(s.ARROW_PATH).convert_alpha()  # chargement de l'image de flèche
        self.ROAD_ARROW = pygame.transform.smoothscale(arrow, (s.ROAD_WIDTH*0.7, s.ROAD_WIDTH*0.7))  # ajustement de la taille des flèches pour les routes
        self.CAR_ARROW = pygame.transform.smoothscale(arrow, (s.CAR_WIDTH*0.8, s.CAR_WIDTH*0.8))  # pour les voitures

        self.off_set = (0, 0)  # décalage par rapport à l'origine, pour bouger la simulation
        self.dragging = False  # si l'utilisateur est en train de bouger la simulation
        self.mouse_last = (0, 0)  # dernière coordonnées de la souris

    def start_loop(self):
        """Ouvre une fenêtre et lance la simulation."""
        while not self.over:  # tant que la simulation n'est pas terminée
            for event in pygame.event.get():  # on regarde les dernières actions de l'utilisateur
                self.manage_event(event)

            self.surface.fill(self.bg_color)  # efface tout

            self.show_roads(self.roads)  # affiche les routes

            if self.paused:  # si en pause
                for road in self.roads:
                    for car in road.cars:
                        self.show_car(car)  # affichage des voitures de la route
                self.show_info(self.info_to_show)  # affiche les informations
                pygame.display.flip()  # actualisation de la fenêtre
                self.clock.tick(self.FPS)  # pause d'une durée dt
                continue  # saute la suite de la boucle et passe à l'itération suivante

            for road in self.roads:
                # affichage des voitures de la route
                for car in road.cars:
                    self.show_car(car)

                if road.traffic_light is not None:
                    road.traffic_light.update(t=self.t)  # actualisation de l'éventuel feu de la route
                    self.show_traffic_light(road.traffic_light)  # affichage du feu

                # actualisation des coordonnées des voitures de la route
                road.update_cars(dt=self.speed_ajusted_dt, leader_coords=self.get_leader_coords(road))

                # éventuelle création d'une nouvelle voiture au début de la route
                args_crea = {"t": self.t}
                args_fact = {"t": self.t, "last_car": road.cars[-1] if road.cars else None}
                new_car = road.car_factory.factory(args_crea=args_crea, args_fact=args_fact)
                road.new_car(new_car)

            self.t += self.speed_ajusted_dt  # actualisation du suivi du temps
            self.show_info(self.info_to_show)  # affiche les informations
            pygame.display.flip()  # actualisation de la fenêtre
            self.clock.tick(self.FPS)  # pause d'une durée dt

        self.print_simulation_info()  # afficher les informations quand on quitte

    def start(self):
        """Ouvre une fenêtre et lance la simulation, affiche l'état de la simulation en cas d'erreur."""
        try:
            self.start_loop()
        except Exception as exeption:
            if s.LOGS:
                self.print_simulation_info()
                print(f"\n*** Erreur : {exeption} ***\n\n{traceback.format_exc()}")

    def print_simulation_info(self):
        """Affiche l'ensemble des objects et leurs principaux attributs dans la sortie standard."""
        if s.LOGS:
            print(f"\n--- Simulation Infos ---\n\n{self.size = }\n{self.t = }\n{self.FPS = }\n{self.dt = }\n{self.speed = }\n{self.speed_ajusted_dt = }\n{self.paused = }\n{self.over = }\n{self.dragging = }\n{self.off_set = }\n{self.road_graph = }\n")
            for road in self.roads:
                print(f"\n{road} :\n    TrafficLight : {road.traffic_light}\n    Cars :")
                for car in road.cars:
                    print(f"        {car}")
                print(f"    CarFactory : {road.car_factory}\n    CarSorter : {road.car_sorter}")

    def show_info(self, info):
        """Affiche des informations en haut à gauche de la fenêtre."""
        text_width, text_height = self.FONT.size(info)
        draw_rect(self.surface, s.INFOS_BG_COLOR, (0, 0), text_width + 30, text_height + 20)
        print_text(self.surface, s.FONT_COLOR, (10, 10), info, self.FONT)

    @property
    def info_to_show(self):
        """Renvoie les informations à afficher sur la fenêtre : horloge, nombre d'images, vitesse..."""
        return f"t = {round(self.t, 2):<7} = {round(self.t//60):>02}m{round(self.t) % 60:02}s | vitesse = ×{self.speed:<4} | {'en pause' if self.paused else 'en cours'} | ESPACE : mettre en pause, FLÈCHE DROITE : ralentir, FLÈCHE GAUCHE : accélérer, ENTRER : recentrer"

    def manage_event(self, event):
        """Gère les conséquences en cas d'un certain évenement pygame (pause, changement de vitesse, déplacement...)."""
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
            elif event.key in (pygame.K_LEFT, pygame.K_DOWN) and self.speed >= 0.5:
                # si l'utilisateur appuie sur la flèche gauche ou bas, ralentir jusqu'à 0.25
                self.speed = round(self.speed / 2, 2)
                self.speed_ajusted_dt = round(self.speed_ajusted_dt / 2, 2)
            elif event.key in (pygame.K_RIGHT, pygame.K_UP) and self.speed <= 16:
                # si l'utilisateur appuie sur la flèche droite ou haut, accélérer jusqu'à 32
                self.speed = round(self.speed * 2, 2)
                self.speed_ajusted_dt = round(self.speed_ajusted_dt * 2, 2)
            elif event.key == pygame.K_RETURN:
                # si l'utilisateur appuie sur entrer, recentrer la fenêtre
                self.off_set = (0, 0)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # si l'utilisateur clique
            x, y = pygame.mouse.get_pos()
            x0, y0 = self.off_set
            self.mouse_last = (x - x0, y - y0)
            self.dragging = True

        elif event.type == pygame.MOUSEMOTION and self.dragging:
            # bouge la simulation
            x1, y1 = self.mouse_last
            x2, y2 = pygame.mouse.get_pos()
            self.off_set = (x2 - x1, y2 - y1)

        elif event.type == pygame.MOUSEBUTTONUP:
            # si l'utilisateur ne clique plus
            self.dragging = False

    def show_car(self, car: Car):
        """Affiche une voiture."""
        draw_polygon(self.surface, car.color, car.coins, self.off_set)
        if s.CAR_SHOW_ARROW:  # si on affiche la direction de la voiture
            rotated_arrow = pygame.transform.rotate(self.CAR_ARROW, car.road.angle)
            draw_image(self.surface, rotated_arrow, car.road.dist_to_pos(car.d), self.off_set)
        elif s.CAR_SHOW_SPEED_MS or s.CAR_SHOW_SPEED_KMH:  # si on affiche la vitesse de la voiture
            coeff = 3.6 if s.CAR_SHOW_SPEED_KMH else 1
            text = str(round(coeff * car.v / s.SCALE))
            text_width, text_height = self.CAR_FONT.size(text)
            x = car.x - text_width / 2
            y = car.y - text_height / 2
            print_text(self.surface, s.FONT_COLOR, (x, y), text, self.CAR_FONT, off_set=self.off_set)
        elif s.CAR_SHOW_ID:  # si on affiche l'id de la voiture
            text = str(car.id)
            text_width, text_height = self.CAR_FONT.size(text)
            x = car.x - text_width / 2
            y = car.y - text_height / 2
            print_text(self.surface, s.FONT_COLOR, (x, y), text, self.CAR_FONT, off_set=self.off_set)

    def show_roads(self, road_list):
        """Affiche des routes."""
        for road in road_list:
            if isinstance(road, Road):
                draw_polygon(self.surface, road.color, road.coins, self.off_set)

                rotated_arrow = pygame.transform.rotate(self.ROAD_ARROW, road.angle)

                for arrow_coord in road.arrows_coords:
                    x, y, _ = arrow_coord
                    draw_image(self.surface, rotated_arrow, (x, y), self.off_set)
            elif isinstance(road, ArcRoad):
                self.show_roads(road.sroads)

    def show_traffic_light(self, traffic_light):
        """Affiche les feux de signalisations."""
        if not traffic_light.static:
            color = {0: s.TL_RED, 1: s.TL_ORANGE, 2: s.TL_GREEN}[traffic_light.state]
            draw_polygon(self.surface, color, traffic_light.coins, self.off_set)

    def create_road(self, **kw):
        """Créer une route."""
        start, end, vdstart, vdend, car_factory, color, w, obj_id = kw.get("start", (0, 0)), kw.get("end", (0, 0)), kw.get("vdstart"), kw.get("vdend"), kw.get("car_factory"), kw.get("color", s.ROAD_COLOR), kw.get("width", s.ROAD_WIDTH), kw.get("id")
        if isinstance(start, int):  # si l'argument start est un id de route
            rstart = get_by_id(start)
            start = rstart.end
            vdstart = rstart.vd
        if isinstance(end, int):  # si l'argument end est un id de route
            rend = get_by_id(end)
            end = rend.start
            vdend = rend.vd
        if kw["type"] == "road":  # si on crée une route droite
            traffic_light, wa = kw.get("traffic_light"), kw.get("with_arrows", True)
            road = Road(start, end, width=w, color=color, with_arrows=wa, car_factory=car_factory, traffic_light=traffic_light, obj_id=obj_id)
        else:  # si on crée une route courbée
            n = kw.get("n", s.ARCROAD_N)
            road = ArcRoad(start, end, vdstart, vdend, n, width=w, color=color, car_factory=car_factory, obj_id=obj_id)
        self.roads.append(road)
        return road

    def create_roads(self, road_list: list[dict]):
        """Créer des routes, renvoie la liste des routes.

        Les éléments de ``road_list`` sont des dictionnaires de la forme :\n
        - pour une route droite, ``{"id": int, "type": "road", "start": (float, float) | int, "end": (float, float) | int, "v_max": float (optionnel), "car_factory": CarFactory (optionnel), "traffic_light": TrafficLight (optionnel), "with_arrows": bool (optionnel)}``
        - pour une route courbée, ``{"id": int, "type": "arcroad", "start": (float, float) | int, "vdstart": (float, float), "end": (float, float) | int, "vdend": (float, float), "v_max": float (optionnel), "n": int (optionnel), "car_factory": CarFactory (optionnel)}``

        avec :\n
        - ``id`` l'identifiant de la route
        - ``start`` les coordonnées en pourcentages de la fenêtre du début de la route, ou l'identifiant d'une route dont la fin servira de début
        - ``end`` les coordonnées en pourcentages de la fenêtre de la fin de la route, ou l'identifiant d'une route dont le début servira de fin
        - ``v_max`` l'éventuelle limite de vitesse de la route, par défaut ``V_MAX`` pour road et ``V_MAX*ARCROAD_V_MAX_COEFF``
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

    def get_leader_coords(self, road: Road, avg=s.GET_LEADER_COORDS_METHOD_AVG):
        """Renvoie la distance et la vitesse d'un éventuel leader de la première voiture de la route.

        Si GET_LEADER_COORDS_METHOD_AVG est True, renvoie la moyenne des distances, depuis la fin de la route, et des vitesses des dernières voitures des prochaines routes, pondérée par la probabilité que la première voiture aille sur ces routes.

        Sinon, renvoie celles de la dernière voiture de la prochaine route de la première voiture de la route."""
        if avg:  # si GET_LEADER_COORDS_METHOD_AVG est True
            next_roads_probs = self.road_graph[road.id]  # récupération des prochaines routes et de leurs probas

            if next_roads_probs is None:  # si pas de prochaine route
                return None
            elif isinstance(next_roads_probs, int):  # si un seul choix de prochaine route
                next_roads_probs = {next_roads_probs: 1}

            d, v = 0, 0  # initialisation de d et v pour la moyenne

            for next_road_id in next_roads_probs:  # pour chaque prochaine route
                prob = next_roads_probs[next_road_id]  # on récupère la probabilité
                next_road = get_by_id(next_road_id)

                if next_road.cars:  # si elle contient des voitures, on prend les coordonnées de la première
                    next_car = next_road.cars[-1]
                    next_d, next_v = next_car.d, next_car.v
                    d += prob*next_d
                    v += prob*next_v
                else:  # sinon, on cherche plus loin
                    next_avg_leading_car_coords = self.get_leader_coords(next_road)
                    if next_avg_leading_car_coords is not None:  # si toujours rien, on s'arrête
                        d += prob*(next_avg_leading_car_coords[0] + next_road.length)
                        v += prob*next_avg_leading_car_coords[1]

            return (d, v) if d != 0 else None

        else:  # si GET_LEADER_COORDS_METHOD_AVG est False

            next_road = road.cars[0].next_road

            if next_road is None:
                return None
            elif next_road.cars:
                last_car = next_road.cars[-1]
                return last_car.d, last_car.v
            else:
                d, v = self.get_leader_coords(next_road, avg=True)
                return d + next_road.length, v

