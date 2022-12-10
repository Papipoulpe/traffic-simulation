from res import *


# Général

LOGGING_LEVEL = 1  # niveau de logging

# Simulation

WIN_WIDTH = 1440  # largeur de la fenêtre de simulation
WIN_HEIGHT = 840  # hauteur de la fenêtre de simulation
BG_COLOR = FOND_BLEU_M  # couleur de l'arrière plan de la fenêtre
INFOS_BG_COLOR = FOND_BLEU_M_TEXTE  # couleur de l'arrière plan du texte
FPS = 60  # images par secondes de la simulation
SPEED = 1

# Ressources

FONT_PATH = FONT  # chemin à la police de caractère du texte
FONT_SIZE = 15  # taille du texte
FONT_COLOR = BLACK  # couleur du texte
ARROW_PATH = ARROW  # chemin à l'image de flèche
ARROW_SIZE = (15, 15)  # taille des flèches
ARROW_RARETE = 100  # inverse de la fréquence des flèches

# Routes

ROAD_WIDTH = 30  # largeur des routes
ROAD_COLOR = ROUTE_BLEU  # couleur des routes
DEF_ARCROAD_N = 10  # nombre de routes droites par défaut pour les routes courbées

# Voitures

CAR_A = 0  # accéleration par défaut des voitures
CAR_V = 50  # vitesse par défaut des voitures
CAR_COLOR = VOITURE_BLEUVERT  # couleur par défaut des voitures
CAR_WIDTH = 18  # largeur par défaut des voitures
CAR_LENGTH = 30  # longueur par défaut des voitures
CAR_RAND_COLOR_MIN = 0  # niveau minimum de rgb pour les couleurs aléatoires des voitures
CAR_RAND_COLOR_MAX = 210  # niveau maximum de rgb pour les couleurs aléatoires des voitures
CAR_RAND_LENGTH_MIN = 20  # niveau minimum pour les longueurs aléatoires des voitures
CAR_RAND_LENGTH_MAX = 45  # niveau maximum pour les longueurs aléatoires des voitures
CAR_RAND_WIDTH_MIN = 18  # niveau minimum pour les largeurs aléatoires des voitures
CAR_RAND_WIDTH_MAX = 24  # niveau maximum pour les largeurs aléatoires des voitures

# Intelligent Driver Model

DD_MIN = 10  # distance minimum entre deux voitures
V_MAX = 300  # vitesse maximum d'une voiture
A_MAX = 40  # accéleration maximum d'une voiture
A_MIN = 30  # décélération minimum d'une voiture
A_EXP = 4  # exposant de l'accéleration, contrôle la douceur
T_REACT = 0.1  # temps de réaction du conducteur

# Traffic Lights

TL_DELAY = 8  # temps entre rouge et vert
TL_WIDTH = 5  # largeur du trait du feu
