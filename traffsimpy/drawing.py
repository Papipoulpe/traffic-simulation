import pygame
from pygame import gfxdraw as gfx

from .math_and_util import *


def draw_polygon(surface: pygame.Surface, color: Couleur, points: tuple[Vecteur, ...], off_set: Vecteur = npz(2)):
    """
    Dessine un polygône rempli.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du polygone
    :param points: coordonnées des points
    :param off_set: décalage par rapport à l'origine
    """
    points_with_off_set = [p + off_set for p in points]
    gfx.filled_polygon(surface, points_with_off_set, color)
    gfx.aapolygon(surface, points_with_off_set, color)


def draw_empty_polygon(surface: pygame.Surface, color: Couleur, points: tuple[Vecteur, ...], off_set: Vecteur = npz(2)):
    """
    Dessine un polygône vide.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du trait
    :param points: coordonnées des points
    :param off_set: décalage par rapport à l'origine
    """
    points_with_off_set = [p + off_set for p in points]
    gfx.aapolygon(surface, points_with_off_set, color)


def draw_line(surface: pygame.Surface, color: Couleur, start: Vecteur, end: Vecteur, off_set: Vecteur = npz(2)):
    """
    Dessine un segment.

    :param surface: surface surlaquelle dessiner
    :param color: couleur du trait
    :param start: coordonnées du début du segment
    :param end: coordonnées de la fin du segment
    :param off_set: décalage par rapport à l'origine
    """
    x1, y1 = start + off_set
    x2, y2 = end + off_set
    gfx.line(surface, int(x1), int(y1), int(x2), int(y2), color)


def draw_rect(surface: pygame.Surface, color: Couleur, up_left_corner: Vecteur, width: float, heigth: float,
              off_set: Vecteur = npz(2)):
    """
    Dessine un rectangle rempli, sans rotation.

    :param surface: surface sur laquelle dessiner
    :param color: couleur du rectangle
    :param up_left_corner: coordonnées du coin supérieur gauche
    :param width: largeur
    :param heigth: hauteur
    :param off_set: décalage par rapport à l'origine
    """
    w, wh, h = npa(((width, 0), (width, heigth), (0, heigth)))
    points = (up_left_corner, up_left_corner + w, up_left_corner + wh, up_left_corner + h)
    draw_polygon(surface, color, points, off_set)


def draw_circle(surface: pygame.Surface, color: Couleur, center: Vecteur, radius: int, off_set: Vecteur = npz(2)):
    """
    Dessine un disque.

    :param surface: surface surlaquelle dessiner
    :param color: couleur du cercle
    :param center: coordonnées du centre
    :param radius: rayon
    :param off_set: décalage par rapport à l'origine
    """
    x, y = center + off_set
    gfx.filled_circle(surface, round(x), round(y), round(radius), color)
    gfx.aacircle(surface, round(x), round(y), round(radius), color)


def draw_text(surface: pygame.Surface, color: Couleur, up_left_corner: Vecteur, text: str, font: pygame.font.Font,
              anti_aliasing: bool = True, off_set: Vecteur = npz(2)):
    """
    Affiche du texte.

    :param surface: surface sur laquelle afficher
    :param color: couleur du texte
    :param up_left_corner: coordonnées du coin supérieur gauche
    :param text: texte à afficher
    :param font: police de caractère
    :param anti_aliasing: anti_aliasing, True par défaut
    :param off_set: décalage par rapport à l'origine
    """
    a, b = off_set
    x, y = up_left_corner
    rendered = font.render(text, anti_aliasing, color)
    surface.blit(rendered, (x + a, y + b))


def draw_image(surface: pygame.Surface, image, coords: Vecteur, off_set: Vecteur = npz(2)):
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
