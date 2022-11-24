import pygame
from objets import *
from draw_tools import *
import settings as s


class Simulation:
    def __init__(self):
        """Simulation du traffic."""
        self.id = 0  # identifiant
        ids[0] = self
        self.size = s.WIN_WIDTH, s.WIN_HEIGTH
        self.t = 0.0
        self.frame_count = 0
        self.FPS = s.FPS
        self.dt = 1/self.FPS
        self.over = False

        self.roads: list[Road] = []
        self.road_graph = {}

        pygame.init()

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

            self.surface.fill(self.bg_color)  # efface tout

            self.print_infos(f"t = {round(self.t, 2)}")  # affiche l'horloge

            self.show_roads(self.roads)  # affiche les routes

            for road in self.roads:
                road.refresh_cars_coords(dt=self.dt)
                road.new_car(road.car_factory.factory({"t": self.t}, {"t": self.t, "last_car": road.cars[-1] if road.cars != [] else None}))

                for car in road.cars:
                    self.show_car(car)

                for car in road.exiting_cars:
                    new_road = road.car_sorter.sorter(t=self.t)
                    if new_road is not None:
                        new_road.new_car(car)

                road.exiting_cars = []

            pygame.display.flip()
            self.t += self.dt
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
            draw_polygon(self.surface, road.color, road.coins)

            rotated_arrow = pygame.transform.rotate(self.ARROW, road.angle)

            for arrow_coord in road.arrows_coords:
                x, y, _ = arrow_coord
                draw_image(self.surface, rotated_arrow, (x, y))

    def create_road(self, start, end, car_factory: CarFactory = None, color=s.ROAD_COLOR, w=s.ROAD_WIDTH, obj_id=None):
        """Créer une route."""
        road = Road(start, end, width=w, color=color, car_factory=car_factory, obj_id=obj_id)
        self.roads.append(road)
        return road

    def create_roads(self, road_list):
        """Créer des routes droites, renvoie la liste des routes."""
        return [self.create_road(**road) for road in road_list]

    def set_road_graph(self, graph):
        self.road_graph = graph
        for road in self.roads:
            if isinstance(graph[road.id], CarSorter):
                car_sorter = graph[road.id]
            else:
                car_sorter = CarSorter(method=graph[road.id])

            road.car_sorter = car_sorter
