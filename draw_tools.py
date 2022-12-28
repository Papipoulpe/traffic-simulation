import pygame
from pygame import gfxdraw as gfx


def draw_polygon(surface: pygame.Surface, color: (int, int, int), points: (float, float)):
    """
    Dessine un polygone.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du polygone
    :param points: coordonnées des points
    """
    gfx.aapolygon(surface, points, color)
    gfx.filled_polygon(surface, points, color)


def draw_rect(surface: pygame.Surface, color: (int, int, int), up_left_corner: (float, float), width: float, heigth: float):
    """
    Dessine un rectange.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du rectangle
    :param up_left_corner: coordonnées du coin supérieur gauche
    :param width: largeur
    :param heigth: hauteur
    """
    x, y = up_left_corner
    draw_polygon(surface, color, ((x, y), (x + width, y), (x + width, y + heigth), (x, y + heigth)))


def print_text(surface: pygame.Surface, color: (int, int, int), coords: (float, float), text: str, font: pygame.font.Font, anti_aliasing: bool = True):
    """
    Affiche du texte.

    :param surface: surface sur laquelle afficher
    :param color: couleur du texte
    :param coords: coordonnées supérieures gauches
    :param text: texte à afficher
    :param font: police de caractère
    :param anti_aliasing: anti_aliasing, True par défaut
    """
    rendered = font.render(text, anti_aliasing, color)
    surface.blit(rendered, coords)


def draw_image(surface: pygame.Surface, image, coords: (float, float)):
    """
    Affiche une image.

    :param surface: surface sur laquelle afficher
    :param image: image à afficher
    :param coords: coordonées du centre de l'image
    """
    surface.blit(image, image.get_rect(center=image.get_rect(center=coords).center))
