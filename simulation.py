import pygame
from objets import *
from draw_tools import *
import settings as s
from res import *


class Simulation:
    def __init__(self, win_title="Traffic Simulation"):
        """Simulation du traffic."""
        self.id = 0  # identifiant
        ids[0] = self
        self.size = s.WIN_WIDTH, s.WIN_HEIGHT  # taille de la fenêtre
        self.t = 0.0  # suivi du temps
        self.frame_count = 0  # suivi du nombre d'image
        self.FPS = s.FPS
        self.dt = 1/self.FPS
        self.over = False

        self.roads = []
        self.road_graph = {}

        pygame.init()
        pygame.display.set_caption(win_title)

        self.surface = pygame.display.set_mode(self.size)
        self.clock = pygame.time.Clock()
        self.surfrect = self.surface.get_rect()
        self.bg_color = s.BG_COLOR
        self.surface.fill(self.bg_color)
        self.font = pygame.font.Font(s.FONT_PATH, s.FONT_SIZE)
        arrow = pygame.image.load(s.ARROW_PATH).convert_alpha()
        self.ARROW = pygame.transform.smoothscale(arrow, s.ARROW_SIZE)

    def start_loop(self):
        """Ouvre une fenêtre et lance la simulation."""
        while not self.over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.over = True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.over = True

            if pygame.mouse.get_pressed()[0]:
                continue

            self.surface.fill(self.bg_color)  # efface tout

            self.print_infos(f"t = {round(self.t, 2):<10} n = {self.frame_count}")  # affiche l'horloge et le nombre d'image

            self.show_roads(self.roads)  # affiche les routes
            self.show_traffic_lights()  # affiche les feux de signalisation

            for road in self.roads:
                if road.traffic_light:
                    road.traffic_light.update(t=self.t)

                road.update_cars_coords(self.dt, self.get_avg_leading_car_coords(road))

                new_car = road.car_factory.factory({"t": self.t}, {"t": self.t, "last_car": road.cars[-1] if road.cars else None})
                if new_car is not None:
                    road.new_car(new_car)

                for car in road.cars:
                    self.show_car(car)

                for car in road.exiting_cars:
                    self.show_car(car)
                    new_road = road.car_sorter.sorter(t=self.t)
                    if new_road is not None:
                        new_road.new_car(car)

                road.exiting_cars = []

            pygame.display.flip()
            self.t += self.dt
            self.frame_count += 1
            self.clock.tick(self.FPS)

    def print_infos(self, info):
        """Affiche des infos en haut à gauche de la fenêtre."""
        draw_rect(self.surface, s.INFOS_BG_COLOR, (0, 0), 300, 40)
        print_text(self.surface, s.FONT_COLOR, (10, 10), info, self.font)

    def show_car(self, car: Car):
        """Dessine une voiture."""
        draw_polygon(self.surface, car.color, car.coins)

    def show_roads(self, road_list):
        """Affiche des routes."""
        for road in road_list:
            log(f"Showing {road}", 2)
            if isinstance(road, Road):
                draw_polygon(self.surface, road.color, road.coins)

                rotated_arrow = pygame.transform.rotate(self.ARROW, road.angle)

                for arrow_coord in road.arrows_coords:
                    x, y, _ = arrow_coord
                    draw_image(self.surface, rotated_arrow, (x, y))
            elif isinstance(road, ArcRoad):
                self.show_roads(road.roads)

    def create_road(self, **kw):
        """Créer une route."""
        if kw["type"] == "road":  # si on crée une route droite
            start, end, car_factory, traffic_light, color, wa, w, obj_id = kw.get("start"), kw.get("end"), kw.get("car_factory"), kw.get("traffic_light"), kw.get("color", s.ROAD_COLOR), kw.get("with_arrows", True), kw.get("width", s.ROAD_WIDTH), kw.get("id")
            road = Road(start, end, width=w, color=color, with_arrows=wa, car_factory=car_factory, traffic_light=traffic_light, obj_id=obj_id)
        else:  # si on crée une route courbée
            start, end, vdstart, vdend, n, car_factory, color, w, obj_id = kw.get("start"), kw.get("end"), kw.get("vdstart"), kw.get("vdend"), kw.get("n", s.DEF_ARCROAD_N), kw.get("car_factory"), kw.get("color", s.ROAD_COLOR), kw.get("width", s.ROAD_WIDTH), kw.get("id")
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
        log(f"Creating {road}")
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

    def show_traffic_lights(self):
        for road in self.roads:
            if road.traffic_light:
                if road.traffic_light.green:
                    color = FEU_STOP_VERT
                else:
                    color = FEU_STOP_ROUGE

                draw_polygon(self.surface, color, road.traffic_light.coins)

    def get_avg_leading_car_coords(self, road: Road):
        """Renvoie la moyenne des distances depuis la fin de la route et des vitesses des dernières voitures des
        prochaines routes, pondérée par la probabilité que la première voiture aille sur ces routes."""
        next_roads_probs = self.road_graph[road.id]

        if next_roads_probs is None:  # si pas de prochaine route
            return None
        elif isinstance(next_roads_probs, int):  # si un seul choix de prochaine route
            next_roads_probs = {next_roads_probs: 1}

        d, v = 0, 0

        for road_id in next_roads_probs:
            prob = next_roads_probs[road_id]
            next_road = get_by_id(road_id)

            if next_road.cars:
                next_car = next_road.cars[-1]
                next_d, next_v = next_car.d + road.length, next_car.v
                d += prob*next_d
                v += prob*next_v
            else:
                return None

        return d, v
