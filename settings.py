from ressources import *

# Simulation

LOGS = True  # si on affiche les détails de la simulation et les erreurs quand on passe en pause, quand le programme est quitté ou se plante
BG_COLOR = FOND_BLEU_M  # couleur de l'arrière plan de la fenêtre
INFOS_BG_COLOR = FOND_BLEU_M_TEXTE  # couleur de l'arrière plan du texte
FPS = 60  # Hz, images par secondes de la simulation
SPEED = 1  # vitesse de la simulation
SCALE = 10  # pixels/m, échelle de la simulation
GET_LEADER_COORDS_METHOD_AVG = True  # False = voiture la plus proche sur les prochaines routes, True = moyenne pondérée par les probas d'aller sur les prochaines routes

# Ressources

FONT_PATH = FONT  # chemin à la police de caractère du texte
FONT_SIZE = 15  # pixels, taille du texte
FONT_COLOR = BLACK  # couleur du texte
ARROW_PATH = ARROW  # chemin à l'image de flèche

# Routes

ROAD_WIDTH = 3  # m, largeur des routes
ROAD_COLOR = ROUTE_BLEU  # couleur des routes
ARCROAD_N = 10  # nombre de routes droites pour les routes courbées
ARCROAD_V_MAX_COEFF = 0.45  # coefficient de ralentissement pour les routes courbées, facteur de V_MAX
ARROW_RARETE = 100  # inverse de la fréquence des flèches

# Voitures

CAR_A = 0  # m/s², accéleration par défaut des voitures
CAR_V = None  # m/s, vitesse par défaut des voitures (50 km/h = 13.9 m/s, 30 km/h = 8.3 m/s), None pour V_MAX de la route
CAR_WIDTH = 1.8  # m, largeur par défaut des voitures
CAR_LENGTH = 3  # m, longueur par défaut des voitures
CAR_COLOR = VOITURE_BLEUVERT  # couleur par défaut des voitures
CAR_SHOW_ARROW = False  # si on affiche la direction de chaque voiture sur son toit
CAR_SHOW_ID = True  # si on affiche l'id de chaque voiture sur son toit
CAR_SHOW_SPEED_MS = False  # si on affiche la vitesse de chaque voiture sur son toit en m/s
CAR_SHOW_SPEED_KMH = False  # si on affiche la vitesse de chaque voiture sur son toit en km/h
CAR_RAND_COLOR_MIN = 70  # niveau minimum de r, g et b pour les couleurs aléatoires des voitures
CAR_RAND_COLOR_MAX = 180  # niveau maximum de r, g et b pour les couleurs aléatoires des voitures
CAR_RAND_LENGTH_MIN = 2  # m, niveau minimum pour les longueurs aléatoires des voitures
CAR_RAND_LENGTH_MAX = 4.5  # m, niveau maximum pour les longueurs aléatoires des voitures
CAR_RAND_WIDTH_MIN = 1.8  # m, niveau minimum pour les largeurs aléatoires des voitures
CAR_RAND_WIDTH_MAX = 2.4  # m, niveau maximum pour les largeurs aléatoires des voitures

# Intelligent Driver Model

DELTA_D_MIN = 2  # m, distance minimum entre deux voitures
V_MAX = 13.9  # m/s, limite de vitesse par défaut des routes droites (50 km/h = 13.9 m/s, 30 km/h = 8.3 m/s)
A_MAX = 1  # m/s², accéleration maximum d'une voiture
A_MIN = 1.5  # m/s², décélération minimum d'une voiture
A_MIN_CONF = 10  # m/s², décélération confortable d'une voiture
A_EXP = 4  # exposant de l'accéleration, contrôle la douceur
T_REACT = 1  # s, temps de réaction du conducteur

# Traffic Lights

TL_RED_DELAY = 30  # s, durée du feu rouge
TL_ORANGE_DELAY = 4  # s, durée du feu orange
TL_GREEN_DELAY = TL_RED_DELAY - TL_ORANGE_DELAY  # s, durée du feu vert
TL_WIDTH = 5  # pixels, largeur du trait du feu
TL_RED = FEU_ROUGE  # couleur du feu rouge
TL_ORANGE = FEU_ORANGE  # couleur du feu orange
TL_GREEN = FEU_VERT  # couleur du feu vert
TL_ORANGE_SLOW_DOWN_COEFF = 0.5  # coefficient de ralentissement du feu orange, un coefficient plus grand ralentit plus

# Mise à l'échelle et finalisation

ROAD_WIDTH, CAR_A, CAR_WIDTH, CAR_LENGTH, CAR_RAND_WIDTH_MAX, CAR_RAND_WIDTH_MIN, CAR_RAND_LENGTH_MAX, CAR_RAND_LENGTH_MIN, DELTA_D_MIN, V_MAX, A_MAX, A_MIN = ROAD_WIDTH * SCALE, CAR_A * SCALE, CAR_WIDTH * SCALE, CAR_LENGTH * SCALE, CAR_RAND_WIDTH_MAX * SCALE, CAR_RAND_WIDTH_MIN * SCALE, CAR_RAND_LENGTH_MAX * SCALE, CAR_RAND_LENGTH_MIN * SCALE, DELTA_D_MIN * SCALE, V_MAX * SCALE, A_MAX * SCALE, A_MIN * SCALE
if CAR_V:
    CAR_V *= SCALE
else:
    CAR_V = V_MAX
