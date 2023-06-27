from .constants import *
import yaml


class SimulationConfiguration:
    def __init__(self):
        """Paramètres de la simulation."""
        # Affichage
        self.print_detailed_logs = False  # si on affiche les détails de la simulation quand l'utilisateur met en pause ou quand le programme s'arrête
        self.print_errors = True  # si on affiche les erreurs quand le programme se plante
        self.background_color = BLUE_BG  # couleur de l'arrière plan de la fenêtre
        self.info_background_color = BLUE_TXT_BG  # couleur de l'arrière plan du texte
        self.show_infos = True  # si on affiche le suivi du temps, la vitesse et l'état de la simulation
        self.show_scale = True  # si on affiche l'échelle de l'espace
        self.show_heavy_traffic_area = True  # si on affiche les zones où les collisions sont détectées

        # Simulation
        self.fps = 60  # Hz, nombre d'images par seconde initial de la simulation
        self.speed = 1  # vitesse initiale de la simulation
        self.max_speed = 4  # vitesse maximum possible, peu d'effets au-delà de 4 pour un processeur classique avec affichage
        self.scale = 10  # pixels/m, échelle de la simulation
        self.average_leaders = False  # méthode pour déterminer le leader de la première voiture d'une route (moyenne/plus proche)
        self.use_hitboxes = True  # si la simulation utilise les hitbox et hurtbox des voitures pour éviter les collisions
        self.screenshot_type = "jpg"  # format des captures d'écran : jpg, png, bmp ou tga

        # Ressources
        self.font_path = DEF_FONT_PATH  # chemin à la police de caractère du texte
        self.font_size = 15  # pixels, taille du texte
        self.font_color = BLACK  # couleur du texte
        self.arrow_path = DEF_ARROW_PATH  # chemin à l'image de flèche

        # Routes
        self.road_width = 3  # m, largeur des routes
        self.road_color = BLUE_ROAD  # couleur des routes
        self.road_arrow_period = 100  # pixels, période spatiale des flèches
        self.road_transition_size = 1 / 3  # proportion de la route où le v_max des voitures varie continuement vers celui de la prochaine route

        self.arcroad_num_of_sroads = 30  # nombre de routes droites pour les routes courbées
        self.arcroad_deceleration_coeff = 0.7  # coefficient de ralentissement pour les routes courbées, facteur de la limite de vitesse

        # CarFactories
        self.car_fact_force_crea = False  # si les CarFactory continuent de rajouter des voitures sur les routes déjà pleines (/!\ peut énormément ralentir la simulation)
        self.car_fact_rand_color_min = 70  # minimum de r, g et b pour les couleurs aléatoires des voitures
        self.car_fact_rand_color_max = 180  # maximum de r, g et b pour les couleurs aléatoires des voitures
        self.car_fact_rand_length_min = 2.7  # m, minimum pour les longueurs aléatoires des voitures
        self.car_fact_rand_length_max = 7.0  # m, maximum pour les longueurs aléatoires des voitures
        self.car_fact_rand_width_min = 1.8  # m, minimum pour les largeurs aléatoires des voitures
        self.car_fact_rand_width_max = 2.4  # m, maximum pour les largeurs aléatoires des voitures

        # Voitures
        self.car_a = 0  # m/s², accéleration par défaut des voitures
        self.car_v = None  # m/s, vitesse par défaut des voitures (50 km/h = 13.9 m/s, 30 km/h = 8.3 m/s), None pour v_max de la route
        self.car_width = 1.8  # m, largeur par défaut des voitures
        self.car_length = 3  # m, longueur par défaut des voitures
        self.car_color = BLUE_GREEN_CAR  # couleur par défaut des voitures
        self.car_speed_coded_color = True  # si la couleur des voitures représente leurs vitesses (de rouge = lent à bleu = rapide)
        self.a_min = -5.8  # m/s², décélération minimum d'une voiture

        self.car_show_hitboxes = False  # si on affiche les zones de collision (hitbox, hurtbox) des voitures
        self.car_show_bounding_boxes = False  # si on affiche les boites englobantes des voitures
        self.car_show_leader_links = False  # si on affiche les liens entre la voiture et ses leaders
        self.car_show_direction = False  # si on affiche la direction de chaque voiture sur son toit
        self.car_show_id = False  # si on affiche l'id de chaque voiture sur son toit
        self.car_show_speed_ms = False  # si on affiche la vitesse de chaque voiture sur son toit en m/s
        self.car_show_speed_kmh = True  # si on affiche la vitesse de chaque voiture sur son toit en km/h

        # Intelligent Driver Model
        self.delta_d_min = 2  # m, distance minimum entre deux voitures successives d'une même route
        self.v_max = 13.9  # m/s, limite de vitesse des routes droites (50 km/h = 13.9 m/s, 30 km/h = 8.3 m/s)
        self.a_max = 1  # m/s², accéleration maximum d'une voiture
        self.a_min_conf = 1.5  # m/s², décélération confortable d'une voiture en valeur absolue
        self.a_exp = 4  # exposant de l'accéleration, contrôle la "douceur"
        self.t_react = 1  # s, temps de réaction du conducteur

        # Feu de signalisation et panneau stop
        self.tl_red_delay = 30  # s, durée du feu rouge
        self.tl_orange_delay = self.tl_red_delay/10  # s, durée du feu orange, éventuellement nulle
        self.tl_green_delay = self.tl_red_delay - self.tl_orange_delay  # s, durée du feu vert
        self.tl_width = 5  # pixels, largeur du trait représentant un feu
        self.tl_red = RED_TL  # couleur du feu rouge
        self.tl_orange = ORANGE_TL  # couleur du feu orange
        self.tl_green = GREEN_TL  # couleur du feu vert
        self.tl_orange_deceleration_coeff = 0.5  # coefficient de ralentissement du feu orange

        self.ss_width = 8  # pixels, largeur du losange représentant un panneau stop
        self.ss_deceleration_coeff = 0.14  # coefficient de ralentissement des panneaux stop
        self.ss_color = RED_SS  # couleur du panneau stop

        # Capteurs
        self.sensor_print_res_at_pause = False  # si les capteurs affichent leurs résulats à chaque mise en pause
        self.sensor_export_res_at_pause = False  # si les capteurs exportent leurs résulats à chaque mise en pause
        self.sensor_color = PURPLE_SENSOR  # couleur du trait représentant un capteur
        self.sensor_width = 3  # largeur du trait représentant un capteur
        self.sensor_file_prefix = ""  # préfixe des fichiers Excel des capteurs

        # Paramètres rapides
        self._debug = False
        self._use_idm = True
        self._presentation_mode = False

        # Données dynamiques
        self.dynamic_data = {"ids": {}, "atm_sensors": {}}

        # Sauvegarde des paramètres par défaut
        self.def_settings = self.__dict__.copy()

    def __str__(self):
        return str(self.__dict__)

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, debug):
        self._debug = debug
        self.print_detailed_logs = debug
        self.car_show_hitboxes = debug
        self.car_show_bounding_boxes = debug
        self.car_show_leader_links = debug
        self.car_show_id = debug
        self.car_show_speed_kmh = debug

    @property
    def use_idm(self):
        return self._use_idm

    @use_idm.setter
    def use_idm(self, use_idm):
        self._use_idm = use_idm
        self.use_hitboxes = use_idm

    @property
    def presentation_mode(self):
        return self._presentation_mode

    @presentation_mode.setter
    def presentation_mode(self, presentation_mode):
        self._presentation_mode = presentation_mode
        self.show_infos = not presentation_mode
        self.show_scale = not presentation_mode

    def load_dict(self, config: dict):
        """Charge une configuration donnée sous forme de dictionnaire."""
        for settings_name in config:
            setattr(self, settings_name, config[settings_name])

    def load_yaml(self, file_path: str):
        """Charge une configuration donnée sous forme de fichier YAML."""
        with open(file_path, "r") as config_file:
            config = yaml.safe_load(config_file)
            self.load_dict(config)


simulation_configuration = SimulationConfiguration()
