import pygame
from pygame import gfxdraw as gfx
from typing import *

Vecteur: TypeAlias = tuple[float, float]  # définiton du type Vecteur = (a, b)
Couleur: TypeAlias = tuple[int, int, int]  # définiton du type Couleur = (r, g, b)


def draw_polygon(surface: pygame.Surface, color: Couleur, points: Sequence[Vecteur], off_set: Vecteur = (0, 0)):
    """
    Dessine un polygone.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du polygone
    :param points: coordonnées des points
    :param off_set: décalage par rapport à l'origine
    """
    a, b = off_set
    points_with_off_set = []

    for point in points:
        x, y = point
        points_with_off_set.append((x + a, y + b))

    gfx.aapolygon(surface, points_with_off_set, color)
    gfx.filled_polygon(surface, points_with_off_set, color)


def draw_rect(surface: pygame.Surface, color: Couleur, up_left_corner: Vecteur, width: float, heigth: float, off_set: Vecteur = (0, 0)):
    """
    Dessine un rectange.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du rectangle
    :param up_left_corner: coordonnées du coin supérieur gauche
    :param width: largeur
    :param heigth: hauteur
    :param off_set: décalage par rapport à l'origine
    """
    x, y = up_left_corner
    draw_polygon(surface, color, ((x, y), (x + width, y), (x + width, y + heigth), (x, y + heigth)), off_set)


def print_text(surface: pygame.Surface, color: Couleur, coords: Vecteur, text: str, font: pygame.font.Font, anti_aliasing: bool = True, off_set: Vecteur = (0, 0)):
    """
    Affiche du texte.

    :param surface: surface sur laquelle afficher
    :param color: couleur du texte
    :param coords: coordonnées supérieures gauches
    :param text: texte à afficher
    :param font: police de caractère
    :param anti_aliasing: anti_aliasing, True par défaut
    :param off_set: décalage par rapport à l'origine
    """
    a, b = off_set
    x, y = coords
    rendered = font.render(text, anti_aliasing, color)
    surface.blit(rendered, (x + a, y + b))


def draw_image(surface: pygame.Surface, image, coords: Vecteur, off_set: Vecteur = (0, 0)):
    """
    Affiche une image.

    :param surface: surface sur laquelle afficher
    :param image: image à afficher
    :param coords: coordonées du centre de l'image
    :param off_set: décalage par rapport à l'origine
    """
    a, b = off_set
    x, y = coords
    surface.blit(image, image.get_rect(center=image.get_rect(center=(x + a, y + b)).center))
