import pygame
from pygame import gfxdraw as gfx

from .math_and_util import *


def draw_polygon(surface: pygame.Surface, color: Color, points: tuple[Coordinates, ...], off_set: Coordinates = npz(2),
                 anti_aliasing: bool = True):
    """Dessine un polygone rempli.

    Args:
        surface: surface sur laquelle dessiner
        color: couleur du polygone
        points: coordonnées des points
        off_set: décalage par rapport à l'origine
        anti_aliasing: anticrénelage
    """
    points_with_off_set = [p + off_set for p in points]
    gfx.filled_polygon(surface, points_with_off_set, color)
    if anti_aliasing:
        gfx.aapolygon(surface, points_with_off_set, color)


def draw_empty_polygon(surface: pygame.Surface, color: Color, points: tuple[Coordinates, ...], off_set: Coordinates = npz(2)):
    """Dessine un polygone vide.

    Args:
        surface: surface sur laquelle dessiner
        color: couleur du trait
        points: coordonnées des points
        off_set: décalage par rapport à l'origine
    """
    points_with_off_set = [p + off_set for p in points]
    gfx.aapolygon(surface, points_with_off_set, color)


def draw_line(surface: pygame.Surface, color: Color, start: Coordinates, end: Coordinates, off_set: Coordinates = npz(2)):
    """Dessine un segment.

    Args:
        surface: surface surlaquelle dessiner
        color: couleur du trait
        start: coordonnées du début du segment
        end: coordonnées de la fin du segment
        off_set: décalage par rapport à l'origine
    """
    x1, y1 = start + off_set
    x2, y2 = end + off_set
    gfx.line(surface, int(x1), int(y1), int(x2), int(y2), color)


def draw_rect(surface: pygame.Surface, color: Color, up_left_corner: Coordinates, width: float, heigth: float,
              off_set: Coordinates = npz(2)):
    """Dessine un rectangle rempli, sans rotation.

    Args:
        surface: surface sur laquelle dessiner
        color: couleur du rectangle
        up_left_corner: coordonnées du coin supérieur gauche
        width: largeur
        heigth: hauteur
        off_set: décalage par rapport à l'origine
    """
    w, wh, h = npa(((width, 0), (width, heigth), (0, heigth)))
    points = (up_left_corner, up_left_corner + w, up_left_corner + wh, up_left_corner + h)
    draw_polygon(surface, color, points, off_set)


def draw_circle(surface: pygame.Surface, color: Color, center: Coordinates, radius: int, off_set: Coordinates = npz(2),
                anti_aliasing: bool = True):
    """Dessine un disque.

    Args:
        surface: surface surlaquelle dessiner
        color: couleur du cercle
        center: coordonnées du centre
        radius: rayon
        off_set: décalage par rapport à l'origine
        anti_aliasing: anticrénelage, si le disque doit être lissé ou
            non
    """
    x, y = center + off_set
    gfx.filled_circle(surface, round(x), round(y), round(radius), color)
    if anti_aliasing:
        gfx.aacircle(surface, round(x), round(y), round(radius), color)


def draw_text(surface: pygame.Surface, color: Color, up_left_corner: Coordinates, text: str, font: pygame.font.Font,
              anti_aliasing: bool = True, off_set: Coordinates = npz(2)):
    """Affiche du texte.

    Args:
        surface: surface sur laquelle afficher
        color: couleur du texte
        up_left_corner: coordonnées du coin supérieur gauche
        text: texte à afficher
        font: police de caractère
        anti_aliasing: anti_aliasing, True par défaut
        off_set: décalage par rapport à l'origine
    """
    a, b = off_set
    x, y = up_left_corner
    rendered = font.render(text, anti_aliasing, color)
    surface.blit(rendered, (x + a, y + b))


def draw_image(surface: pygame.Surface, image, coords: Coordinates, off_set: Coordinates = npz(2)):
    """Affiche une image.

    Args:
        surface: surface sur laquelle afficher
        image: image à afficher
        coords: coordonées du centre de l'image
        off_set: décalage par rapport à l'origine
    """
    a, b = off_set
    x, y = coords
    surface.blit(image, image.get_rect(center=image.get_rect(center=(x + a, y + b)).center))
