from .ressources import *

# Affichage

SHOW_DETAILED_LOGS = True  # si on affiche les détails de la simulation quand on passe en pause ou quand le programme s'arrête
SHOW_ERRORS = True  # si on affiche les erreurs quand le programme se plante
BACKGROUND_COLOR = BLUE_BG  # couleur de l'arrière plan de la fenêtre
INFO_BACKGROUND_COLOR = BLUE_TXT_BG  # couleur de l'arrière plan du texte
SHOW_SCALE = True  # si on affiche l'échelle des distances
SHOW_BUMPING_ZONE = True  # si on affiche les zones où les collisions sont détectées

# Simulation

FPS = 60  # Hz, images par secondes de la simulation
SPEED = 1  # vitesse de la simulation
MAX_SPEED = 4  # vitesse maximum possible, peu d'effets au delà de 4 pour un processeur classique
SCALE = 10  # pixels/m, échelle de la simulation
GET_LEADERS_METHOD_AVG = False  # méthode pour determiner le leader de la première voiture d'une route. True = dernières voitures des prochaines routes, coefficientées par la probabilité que la voiture aille sur ces routes. False = dernière voiture de la prochaine route de la voiture.
USE_BUMPING_BOXES = True  # si la simulation utlise les hitbox et hurtbox des voitures pour éviter les collisions

# Ressources

FONT_PATH = DEF_FONT_PATH  # chemin à la police de caractère du texte
FONT_SIZE = 15  # pixels, taille du texte
FONT_COLOR = BLACK  # couleur du texte
ARROW_PATH = DEF_ARROW_PATH  # chemin à l'image de flèche

# Routes

ROAD_WIDTH = 3  # m, largeur des routes
ROAD_COLOR = BLUE_ROAD  # couleur des routes
ROAD_ARROW_PERIOD = 100  # pixels, période spatiale des flèches
ARCROAD_NUM_OF_SROAD = 10  # nombre de routes droites pour les routes courbées
ARCROAD_V_MAX_COEFF = 0.45  # coefficient de ralentissement pour les routes courbées, facteur de V_MAX
CAR_FACT_FORCE_CREA = False  # /!\ peut énormément ralentir la simulation, si les CarFactory continuent de rajouter des voitures sur les routes lorsqu'elles sont déjà pleines

# Voitures

CAR_A = 0  # m/s², accéleration par défaut des voitures
CAR_V = None  # m/s, vitesse par défaut des voitures (50 km/h = 13.9 m/s, 30 km/h = 8.3 m/s), None pour V_MAX de la route
CAR_WIDTH = 1.8  # m, largeur par défaut des voitures
CAR_LENGTH = 3  # m, longueur par défaut des voitures
CAR_COLOR = BLUE_GREEN_CAR  # couleur par défaut des voitures
CAR_SPEED_CODED_COLOR = False  # si la couleur des voitures représente leurs vitesses (de rouge = lent à bleu = rapide)

CAR_SHOW_BUMPING_BOXES = True  # si on affiche les zones de collision (hitbox, hurtbox) des voitures
CAR_SHOW_LEADER_LINKS = True  # si on affiche les liens entre la voitures et ses leaders
CAR_SHOW_ARROW = False  # si on affiche la direction de chaque voiture sur son toit
CAR_SHOW_ID = False  # si on affiche l'id de chaque voiture sur son toit
CAR_SHOW_SPEED_MS = False  # si on affiche la vitesse de chaque voiture sur son toit en m/s
CAR_SHOW_SPEED_KMH = True  # si on affiche la vitesse de chaque voiture sur son toit en km/h

CAR_LEADERS_COEFF_BUMPING_CARS = 10  # coefficient d'importances des voitures en collisions dans le calcul du leader
CAR_LEADERS_COEFF_IN_FRONT_CAR = 5  # coefficient d'importances de la voiture de devant dans le calcul du leader
CAR_LEADERS_COEFF_NEXT_ROAD_CAR = 5  # coefficient d'importances de la première voiture de la prochaine route dans le calcul du leader

CAR_RAND_COLOR_MIN = 70  # minimum de r, g et b pour les couleurs aléatoires des voitures
CAR_RAND_COLOR_MAX = 180  # maximum de r, g et b pour les couleurs aléatoires des voitures
CAR_RAND_LENGTH_MIN = 2  # m, minimum pour les longueurs aléatoires des voitures
CAR_RAND_LENGTH_MAX = 4.5  # m, maximum pour les longueurs aléatoires des voitures
CAR_RAND_WIDTH_MIN = 1.8  # m, minimum pour les largeurs aléatoires des voitures
CAR_RAND_WIDTH_MAX = 2.4  # m, maximum pour les largeurs aléatoires des voitures

# Intelligent Driver Model

DELTA_D_MIN = 2  # m, distance minimum entre deux voitures
V_MAX = 13.9  # m/s, limite de vitesse par défaut des routes droites (50 km/h = 13.9 m/s, 30 km/h = 8.3 m/s)
A_MAX = 1  # m/s², accéleration maximum d'une voiture
A_MIN = 1.5  # m/s², décélération minimum d'une voiture
A_MIN_CONF = 10  # m/s², décélération confortable d'une voiture
A_EXP = 4  # exposant de l'accéleration, contrôle la "douceur"
T_REACT = 1  # s, temps de réaction du conducteur

# Traffic Lights

TL_RED_DELAY = 30  # s, durée du feu rouge
TL_ORANGE_DELAY = 4  # s, durée du feu orange, éventuellement nulle
TL_GREEN_DELAY = TL_RED_DELAY - TL_ORANGE_DELAY  # s, durée du feu vert
TL_WIDTH = 5  # pixels, largeur du trait du feu
TL_RED = RED_TL  # couleur du feu rouge
TL_ORANGE = ORANGE_TL  # couleur du feu orange
TL_GREEN = GREEN_TL  # couleur du feu vert
TL_ORANGE_SLOW_DOWN_COEFF = 0.5  # coefficient de ralentissement du feu orange, un coefficient plus grand ralentit plus

# Capteurs

SENSOR_EXPORTS_DIRECTORY = "exemples/resultats_capteurs/"
SENSOR_PRINT_RES_AT_PAUSE = False  # si les capteurs affichent leurs résulats à chaque mise en pause
SENSOR_EXPORT_RES_AT_PAUSE = False  # les les capteurs exportent leurs résulats à chaque mise en pause
SENSOR_COLOR = SENSOR_PURPLE  # couleur du trait représentant un capteur
SENSOR_WIDTH = 3  # largeur du trait représentant un capteur

# Mise à l'échelle et finitions

ROAD_WIDTH, CAR_A, CAR_WIDTH, CAR_LENGTH, CAR_RAND_WIDTH_MAX, CAR_RAND_WIDTH_MIN, CAR_RAND_LENGTH_MAX, CAR_RAND_LENGTH_MIN, DELTA_D_MIN, A_MAX, A_MIN = ROAD_WIDTH * SCALE, CAR_A * SCALE, CAR_WIDTH * SCALE, CAR_LENGTH * SCALE, CAR_RAND_WIDTH_MAX * SCALE, CAR_RAND_WIDTH_MIN * SCALE, CAR_RAND_LENGTH_MAX * SCALE, CAR_RAND_LENGTH_MIN * SCALE, DELTA_D_MIN * SCALE, A_MAX * SCALE, A_MIN * SCALE

if CAR_V is not None:
    CAR_V *= SCALE
else:
    CAR_V = V_MAX*SCALE
