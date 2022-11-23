import pygame.draw
from pygame import gfxdraw as gfx


def draw_polygon(surface, color, points):
    """
    Dessine un polygone.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du polygone
    :param points: coordonnées des points
    """
    gfx.aapolygon(surface, points, color)
    gfx.filled_polygon(surface, points, color)


def draw_rect(surface, color, up_left_corner, width, heigth):
    """
    Dessine un rectange.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du rectangle
    :param up_left_corner: coordonnées du coin supérieur gauche
    :param width: largeur
    :param heigth: hauteur
    """
    x, y = up_left_corner
    draw_polygon(surface, color, ((x, y), (x + width, y), (x, y + heigth), (x + width, y + heigth)))


def print_text(surface, color, coords, text, font, anti_aliasing=True):
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


def draw_image(surface, image, coords):
    """
    Affiche une image.

    :param surface: surface sur laquelle afficher
    :param image: image à afficher
    :param coords: coordonées du centre de l'image
    """
    surface.blit(image, image.get_rect(center=image.get_rect(center=coords).center))


def draw_arc(surface, center, radius, start_angle, end_angle, color, width):
    a, b = center
    rect = a - radius, b - radius, 2*radius, 2*radius
    pygame.draw.arc(surface, color, rect, start_angle, end_angle, width)
