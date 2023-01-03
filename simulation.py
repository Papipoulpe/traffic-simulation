from objets import *
from drawing import *
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
                            self.print_simulation_infos()
                    elif event.key in (pygame.K_LEFT, pygame.K_DOWN) and self.speed >= 0.5:
                        # si l'utilisateur appuie sur la flèche gauche ou bas, ralentir jusqu'à 0.25
                        self.speed = round(self.speed/2, 2)
                        self.speed_ajusted_dt = round(self.speed_ajusted_dt/2, 2)
                    elif event.key in (pygame.K_RIGHT, pygame.K_UP) and self.speed <= 16:
                        # si l'utilisateur appuie sur la flèche droite ou haut, accélérer jusqu'à 32
                        self.speed = round(self.speed*2, 2)
                        self.speed_ajusted_dt = round(self.speed_ajusted_dt*2, 2)
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

            self.surface.fill(self.bg_color)  # efface tout

            self.show_roads(self.roads)  # affiche les routes
            self.show_traffic_lights()  # affiche les feux de signalisation

            if self.paused:  # si en pause
                for road in self.roads:
                    for car in road.cars:
                        self.show_car(car)  # affichage des voitures de la route
                    # for car in road.exiting_cars:
                    #     self.show_car(car)  # affichage des voitures quittant la route
                self.frame_count += 1  # actualisation du suivi du nombre d'images
                self.print_infos(self.infos)  # affiche les informations
                pygame.display.flip()  # actualisation de la fenêtre
                self.clock.tick(self.FPS)  # pause d'une durée dt
                continue  # saute la suite de la boucle et passe à l'itération suivante

            for road in self.roads:
                # affichage des voitures de la route
                if road.traffic_light:
                    # actualisation de l'éventuel feu de la route
                    road.traffic_light.update(t=self.t)

                # actualisation des coordonnées des voitures de la route
                road.update_cars(dt=self.speed_ajusted_dt, leader_coords=self.get_leader_coords(road))

                # éventuelle création d'une nouvelle voiture au début de la route
                args_crea = {"t": self.t}
                args_fact = {"t": self.t, "last_car": road.cars[-1] if road.cars else None}
                new_car = road.car_factory.factory(args_crea=args_crea, args_fact=args_fact)
                road.new_car(new_car)

                # gestion des voitures quittant la route
                for car in road.exiting_cars:
                    # self.show_car(car)
                    new_road = road.car_sorter.sorter(t=self.t)  # récupération de la prochaine route
                    if new_road is not None:
                        # s'il y en a une, y ajouter la voiture
                        new_road.new_car(car)

                road.exiting_cars = []  # on vide la liste des voitures sortantes

                for car in road.cars:
                    self.show_car(car)  # affichage des voitures de la route

            self.t += self.speed_ajusted_dt  # actualisation du suivi du temps
            self.frame_count += 1  # actualisation du suivi du nombre d'images
            self.print_infos(self.infos)  # affiche les informations
            pygame.display.flip()  # actualisation de la fenêtre
            self.clock.tick(self.FPS)  # pause d'une durée dt

        self.print_simulation_infos()  # afficher les informations quand on quitte

    def print_simulation_infos(self):
        """Affiche l'ensemble des attributs des objects de la simulation dans la sortie standard."""
        print(f"\n--- Simulation Infos ---\n\n{self.size = }\n{self.t = }\n{self.frame_count = }\n{self.FPS = }\n{self.dt = }\n{self.speed = }\n{self.speed_ajusted_dt = }\n{self.paused = }\n{self.over = }\n{self.dragging = }\n{self.off_set = }\n{self.road_graph = }\n")
        for road in self.roads:
            print(f"\n{road} :\nTrafficLight : {road.traffic_light}\nCars :")
            for car in road.cars:
                print(f"    {car}")
            print("Exiting Cars :")
            for car in road.exiting_cars:
                print(f"    {car}")
            print(f"CarFactory : {road.car_factory}\nCarSorter : {road.car_sorter}")

    def print_infos(self, info):
        """Affiche des informations en haut à gauche de la fenêtre."""
        text_width, text_height = self.FONT.size(info)
        draw_rect(self.surface, s.INFOS_BG_COLOR, (0, 0), text_width + 30, text_height + 20)
        print_text(self.surface, s.FONT_COLOR, (10, 10), info, self.FONT)

    @property
    def infos(self):
        """Renvoie les informations à afficher sur la fenêtre: horloge, nombre d'images, vitesse..."""
        return f"t = {round(self.t, 2):<7} | n = {self.frame_count:<7} | vitesse = ×{self.speed:<4} | {'en pause' if self.paused else 'en cours'} | ESPACE : mettre en pause, FLÈCHE DROITE : ralentir, FLÈCHE GAUCHE : accélérer, ENTRER : recentrer"

    def show_car(self, car: Car):
        """Dessine une voiture."""
        draw_polygon(self.surface, car.color, car.coins, self.off_set)
        if s.CAR_SHOW_ARROW:  # si on affiche la direction de la voiture
            rotated_arrow = pygame.transform.rotate(self.CAR_ARROW, car.road.angle)
            draw_image(self.surface, rotated_arrow, car.road.dist_to_pos(car.d), self.off_set)
        elif s.CAR_SHOW_SPEED_MS or s.CAR_SHOW_SPEED_KMH:  # si on affiche la vitesse de la voiture
            coeff = 3.6 if s.CAR_SHOW_SPEED_KMH else 1
            text = str(round(coeff * car.v / s.SCALE))
            text_width, text_height = self.CAR_FONT.size(text)
            x = car.x - text_width/2
            y = car.y - text_height/2
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

    def show_traffic_lights(self):
        """Affiche les feux de signalisations."""
        for road in self.roads:
            tl: TrafficLight = road.traffic_light
            if tl is not None and not tl.static:
                color = {0: s.TL_RED, 1: s.TL_ORANGE, 2: s.TL_GREEN}[tl.state]
                draw_polygon(self.surface, color, tl.coins, self.off_set)

    def create_road(self, **kw):
        """Créer une route."""
        start, end, vdstart, vdend = kw.get("start"), kw.get("end"), kw.get("vdstart"), kw.get("vdend")
        if isinstance(start, int):  # si l'argument start est un id de route
            rstart = get_by_id(start)
            start = rstart.end
            vdstart = rstart.vd
        if isinstance(end, int):  # si l'argument end est un id de route
            rend = get_by_id(end)
            end = rend.start
            vdend = rend.vd
        if kw["type"] == "road":  # si on crée une route droite
            car_factory, traffic_light, color, wa, w, obj_id = kw.get("car_factory"), kw.get("traffic_light"), kw.get("color", s.ROAD_COLOR), kw.get("with_arrows", True), kw.get("width", s.ROAD_WIDTH), kw.get("id")
            road = Road(start, end, width=w, color=color, with_arrows=wa, car_factory=car_factory, traffic_light=traffic_light, obj_id=obj_id)
        else:  # si on crée une route courbée
            n, car_factory, color, w, obj_id = kw.get("n", s.ARCROAD_N), kw.get("car_factory"), kw.get("color", s.ROAD_COLOR), kw.get("width", s.ROAD_WIDTH), kw.get("id")
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

        if s.GET_LEADER_COORDS_METHOD_AVG:

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

        else:

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

        return (d, v) if d not in (float("inf"), 0) else None
