from res import *


# Général

LOGGING_LEVEL = 3  # niveau de logging

# Simuation

WIN_WIDTH = 1440  # largeur de la fenêtre de simulation
WIN_HEIGTH = 840  # hauteur de la fenêtre de simulation
BG_COLOR = FOND_BLEU_M  # couleur de l'arrière plan de la fenêtre
INFOS_BG_COLOR = FOND_BLEU_M_TEXTE  # couleur de l'arrière plan du texte
FPS = 60  # images par secondes de la simulation

# Ressources

FONT_PATH = "ressources/jbmono.ttf"  # chemin à la police de caractère du texte
FONT_SIZE = 15  # taille du texte
FONT_COLOR = BLACK  # couleur du texte
ARROW_PATH = "ressources/arrow.png"  # chemin à l'image de flèche
ARROW_SIZE = (20, 20)  # taille des flèches
ARROW_RARETE = 100  # inverse de la fréquence des flèches

# Routes

ROAD_WIDTH = 32  # largeur des routes
ROAD_COLOR = ROUTE_BLEU  # couleur des routes

# Voitures

CAR_A = 0  # accéleration par défaut des voitures
CAR_V = 100  # vitesse par défaut des voitures
CAR_COLOR = VOITURE_BLEUVERT  # couleur par défaut des voitures
CAR_WIDTH = 24  # largeur par défaut des voitures
CAR_LENGTH = 30  # longueur par défaut des voitures
CAR_RAND_COLOR_MIN = 0  # niveau minimum de rgb pour les couleurs aléatoires des voitures
CAR_RAND_COLOR_MAX = 230  # niveau maximum de rgb pour les couleurs aléatoires des voitures
CAR_RAND_LENGTH_MIN = 20  # niveau minimum pour les longueurs aléatoires des voitures
CAR_RAND_LENGTH_MAX = 45  # niveau maximum pour les longueurs aléatoires des voitures
CAR_RAND_WIDTH_MIN = 18  # niveau minimum pour les largeurs aléatoires des voitures
CAR_RAND_WIDTH_MAX = 24  # niveau maximum pour les largeurs aléatoires des voitures

# Intelligent Driver Model

DD_MIN = 50  # distance minimum entre deux voitures
V_MAX = 100  # vitesse maximum d'une voiture
A_MAX = 45  # accéleration maximum d'une voiture
A_MIN = 30  # décélération minimum d'une voiture
A_EXP = 4  # exposant de l'accéleration, contrôle la douceur
T_REACT = 0.1  # temps de réaction du conducteur
