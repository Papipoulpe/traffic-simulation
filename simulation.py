from objets import *
from draw_tools import *
import settings as s
import pygame


class Simulation:
    def __init__(self, win_title="Traffic Simulation"):
        """
        Simulation du traffic.

        :param win_title: Titre de la fenêtre
        """
        self.id = 0  # identifiant
        ids[0] = self
        self.size = s.WIN_WIDTH, s.WIN_HEIGHT  # taille de la fenêtre
        self.t = 0.0  # suivi du temps
        self.frame_count = 0  # suivi du nombre d'image
        self.FPS = s.FPS  # images par seconde
        self.dt = 1/self.FPS  # pas de temps
        self.speed_ajusted_dt = self.dt * s.SPEED  # pas de temps ajusté pour la vitesse de la simulation
        self.speed = s.SPEED  # vitesse de la simulation
        self.over = self.paused = False  # si la simulation est finie ou en pause

        self.roads = []  # liste des routes
        self.road_graph = {}  # graphe des routes

        pygame.init()  # initialisation de pygame
        pygame.display.set_caption(win_title)  # modification du titre de la fenêtre

        self.surface = pygame.display.set_mode(self.size)  # création de la fenêtre
        self.clock = pygame.time.Clock()  # création de l'horloge pygame
        self.bg_color = s.BG_COLOR  # couleur d'arrière plan de la fenêtre
        self.surface.fill(self.bg_color)  # coloriage de l'arrière plan
        self.font = pygame.font.Font(s.FONT_PATH, s.FONT_SIZE)  # police d'écriture des informations

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
                if event.type == pygame.QUIT:
                    self.over = True

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # quitte quand on appuie sur escape
                        self.over = True
                    elif event.key == pygame.K_SPACE:
                        # met la simulation en pause quand on appuie sur espace
                        self.paused = not self.paused
                    elif event.key == pygame.K_LEFT and self.speed >= 0.5:
                        # si l'utilisateur appuie sur la flèche gauche, ralentir jusqu'à 0.25
                        self.speed = round(self.speed/2, 2)
                        self.speed_ajusted_dt = round(self.speed_ajusted_dt/2, 2)
                    elif event.key == pygame.K_RIGHT and self.speed <= 16:
                        # si l'utilisateur appuie sur la flèche droite, accélérer jusqu'à 32
                        self.speed = round(self.speed*2, 2)
                        self.speed_ajusted_dt = round(self.speed_ajusted_dt*2, 2)

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

            if self.paused:
                self.print_infos(self.infos)  # affiche l'horloge et le nombre d'image
                pygame.display.flip()  # actualisation de la fenêtre
                self.clock.tick(self.FPS)  # pause d'une durée dt
                continue  # saute le reste de la boucle et passe à l'itération suivante

            self.surface.fill(self.bg_color)  # efface tout

            self.show_roads(self.roads)  # affiche les routes
            self.show_traffic_lights()  # affiche les feux de signalisation

            for road in self.roads:
                if road.traffic_light:
                    # actualisation de l'éventuel feu de la route
                    road.traffic_light.update(t=self.t)

                # actualisation des coordonnées des voitures de la route
                road.update_cars_coords(dt=self.speed_ajusted_dt, leader_coords=self.get_leader_coords(road))

                # éventuelle création d'une nouvelle voiture au début de la route
                args_crea = {"t": self.t}
                args_fact = {"t": self.t, "last_car": road.cars[-1] if road.cars else None}
                new_car = road.car_factory.factory(args_crea=args_crea, args_fact=args_fact)
                road.new_car(new_car)

                # affichage des voitures de la route
                for car in road.cars:
                    self.show_car(car)

                # gestion des voitures quittant la route
                for car in road.exiting_cars:
                    self.show_car(car)
                    new_road = road.car_sorter.sorter(t=self.t)  # récupération de la prochaine route
                    if new_road is not None:
                        # s'il y en a une, y ajouter la voiture
                        new_road.new_car(car)

                road.exiting_cars = []

            self.print_infos(self.infos)  # affiche les informations

            pygame.display.flip()  # actualisation de la fenêtre
            self.t += self.speed_ajusted_dt  # actualisation du suivi du temps
            self.frame_count += 1  # actualisation du suivi du nombre d'images
            self.clock.tick(self.FPS)  # pause d'une durée dt

    def print_infos(self, info):
        """Affiche des informations en haut à gauche de la fenêtre."""
        text_width, text_height = self.font.size(info)
        draw_rect(self.surface, s.INFOS_BG_COLOR, (0, 0), text_width + 30, text_height + 20)
        print_text(self.surface, s.FONT_COLOR, (10, 10), info, self.font)

    @property
    def infos(self):
        """Renvoie les informations à afficher : horloge, nombre d'images, vitesse..."""
        return f"t = {round(self.t, 2):<7} | n = {self.frame_count:<7} | vitesse = ×{self.speed:<4} | {'en pause' if self.paused else 'en cours'} | ESPACE pour mettre en pause, FLÈCHE DROITE ou FLÈCHE GAUCHE pour ralentir ou accélérer"

    def show_car(self, car: Car):
        """Dessine une voiture."""
        draw_polygon(self.surface, car.color, car.coins, self.off_set)
        if s.CAR_SHOW_ARROW:
            rotated_arrow = pygame.transform.rotate(self.CAR_ARROW, car.road.angle)
            draw_image(self.surface, rotated_arrow, car.road.dist_to_pos(car.d), self.off_set)

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
                self.show_roads(road.roads)

    def show_traffic_lights(self):
        """Affiche les feux de signalisations."""
        for road in self.roads:
            tl: TrafficLight = road.traffic_light
            if tl is not None and not tl.static:
                color = {0: s.TL_RED, 1: s.TL_ORANGE, 2: s.TL_GREEN}[tl.state]
                draw_polygon(self.surface, color, tl.coins, self.off_set)

    def create_road(self, **kw):
        """Créer une route."""
        if kw["type"] == "road":  # si on crée une route droite
            start, end, car_factory, traffic_light, color, wa, w, obj_id = kw.get("start"), kw.get("end"), kw.get("car_factory"), kw.get("traffic_light"), kw.get("color", s.ROAD_COLOR), kw.get("with_arrows", True), kw.get("width", s.ROAD_WIDTH), kw.get("id")
            road = Road(start, end, width=w, color=color, with_arrows=wa, car_factory=car_factory, traffic_light=traffic_light, obj_id=obj_id)
        else:  # si on crée une route courbée
            start, end, vdstart, vdend, n, car_factory, color, w, obj_id = kw.get("start"), kw.get("end"), kw.get("vdstart"), kw.get("vdend"), kw.get("n", s.ARCROAD_N), kw.get("car_factory"), kw.get("color", s.ROAD_COLOR), kw.get("width", s.ROAD_WIDTH), kw.get("id")
            if isinstance(start, int):  # si l'argument start est un id de route
                rstart = get_by_id(start)
                start = rstart.end
                vdstart = rstart.vd
            if isinstance(end, int):  # si l'argument end est un id de route
                rend = get_by_id(end)
                end = rend.start
                vdend = rend.vd
            road = ArcRoad(start, end, vdstart, vdend, n, width=w, color=color, car_factory=car_factory, obj_id=obj_id)
        self.roads.append(road)
        return road

    def create_roads(self, road_list):
        """Créer des routes, renvoie la liste des routes."""
        return [self.create_road(**road) for road in road_list]

    def set_road_graph(self, graph):
        self.road_graph = graph
        for road in self.roads:
            val = graph[road.id]
            if isinstance(val, CarSorter):
                car_sorter = val
            elif isinstance(val, int):
                car_sorter = CarSorter(method={val: 1})
            else:
                car_sorter = CarSorter(method=val)

            road.car_sorter = car_sorter

    def get_leader_coords(self, road: Road):
        """Renvoie la moyenne des distances, depuis la fin de la route, et des vitesses des dernières voitures des
        prochaines routes, pondérée par la probabilité que la première voiture aille sur ces routes."""
        next_roads_probs = self.road_graph[road.id]  # récupération des prochaines routes et de leurs probas

        if next_roads_probs is None:  # si pas de prochaine route
            return None
        elif isinstance(next_roads_probs, int):  # si un seul choix de prochaine route
            next_roads_probs = {next_roads_probs: 1}

        if s.GET_LEADER_COORDS_METHOD == "avg":

            d, v = 0, 0

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

        elif s.GET_LEADER_COORDS_METHOD == "min":

            d, v = float("inf"), 0

            for next_road_id in next_roads_probs:  # pour chaque prochaine route
                next_road = get_by_id(next_road_id)

                if next_road.cars:  # si elle contient des voitures, on prend les coordonnées de la première
                    next_car = next_road.cars[-1]
                    next_d, next_v = next_car.d, next_car.v
                    if next_d < d:
                        d = next_d
                        v = next_v
                else:  # sinon, on cherche plus loin
                    next_avg_leading_car_coords = self.get_leader_coords(next_road)
                    if next_avg_leading_car_coords is not None:  # si toujours rien, on s'arrête
                        next_d, next_v = next_avg_leading_car_coords
                        if next_d < d:
                            d = next_d
                            v = next_v

        else:
            raise ValueError('GET_LEADER_COORDS_METHOD doit être "min" ou "avg"')

        return (d, v) if d not in (float("inf"), 0) else None
