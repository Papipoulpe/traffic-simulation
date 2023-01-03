import json
from typing import *
import numpy as np
import settings as s
import webcolors


np.seterr("raise")  # change la gestion des erreurs de maths (division par zéro, racine de réel négatif...)

ids = {-1: None}  # dict des identifiants, initialisé à -1 pour max(id.keys())

Vecteur: TypeAlias = tuple[float, float]  # définiton du type Vecteur = (a, b)
Couleur: TypeAlias = tuple[int, int, int]  # définiton du type Couleur = (r, g, b)


def empty_function(*_, **__): ...  # fonction qui à tout associe rien


def new_id(obj, obj_id: Optional[int] = None) -> int:
    """Créer ou ajoute un identifiant à un objet."""
    if obj_id is None:  # si aucun identifiant fourni, prendre celui après le max
        obj_id = max(ids.keys()) + 1
    ids[obj_id] = obj
    return obj_id


def get_by_id(obj_id: int) -> Any:
    """Renvoie l'objet associé à l'identifiant donné."""
    return ids[obj_id]


def length(point1: Vecteur, point2: Vecteur) -> float:
    """Longueur point1-point2."""
    x1, y1 = point1
    x2, y2 = point2
    return np.sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))


def vect_dir(start: Vecteur, end: Vecteur) -> Vecteur:
    """Renvoyer le vecteur directeur normé d'une droite."""
    x1, y1 = start
    x2, y2 = end
    a, b = x2 - x1, y2 - y1
    n = norme((a, b))
    return a / n, b / n


def norme(vect: Vecteur) -> float:
    """Norme du vecteur."""
    a, b = vect
    return np.sqrt(a * a + b * b)


def vect_norm(vecteur: Vecteur, nouv_norme: float = 1) -> Vecteur:
    """Vecteur normal et normé à un autre vecteur."""
    a, b = vecteur
    coeff = nouv_norme / norme(vecteur)
    return -b * coeff, a * coeff


def angle_of_vect(vect: Vecteur) -> float:
    """Angle du vecteur, en degrés."""
    a, b = vect
    return -float(np.angle([a + 1j * b], deg=True))


def rec_round(obj: Union[Iterable, float], prec: Optional[int] = None) -> Union[Iterable, float]:
    """Arrondi récursif."""
    if isinstance(obj, list) or isinstance(obj, tuple):
        res = []
        for e in obj:
            res.append(rec_round(e, prec))
        if isinstance(obj, tuple):
            res = tuple(res)
        return res
    else:
        return round(obj, prec)


def parse(string: str) -> dict:
    """
    String to dict

    :param string: string to parse
    :return: dict
    """
    return json.loads(string.replace("'", '"'))


def update_taylor(car, dt: float):
    """Calcule les vecteurs du mouvement avec de simples séries de Taylor"""
    car.v = car.v + car.a * dt  # dev de taylor ordre 1
    car.d = car.d + car.v * dt + 1 / 2 * car.a * dt * dt  # dev de taylor ordre 2


def update_taylor_protected(car, dt: float):
    """Calcule les vecteurs du mouvement avec de simples séries de Taylor, en évitant v < 0"""
    car.v = max(car.v + car.a * dt, 0)  # dev de taylor ordre 1, protégé
    car.d = car.d + max(0, car.v * dt + 1 / 2 * car.a * dt * dt)  # dev de taylor ordre 2


def idm(car, avg_leading_car_coords: Optional[tuple[float, float]], dt: float):
    """Intelligent Driver Model. Calcule l'accélération idéale de la voiture."""

    if avg_leading_car_coords:  # si on a un leader
        lead_d, lead_v = avg_leading_car_coords
        delta_d = lead_d - (car.d + car.length)

        if delta_d <= 0:  # si la voiture est en avance, la faire attendre et ralentir
            car.d, car.v, car.a = car.d, 0, car.a
            return

        delta_v = car.v - lead_v
        dd_parfait = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(2 * s.A_MIN_CONF * car.a_max))
        a_interaction = (dd_parfait / delta_d) ** 2
    else:
        a_interaction = 0

    car.a = min(car.a_max * (1 - (car.v / car.road.v_max) ** car.a_exp - a_interaction), car.a_min)

    update_taylor_protected(car, dt)


def intersection_droites(p1: Vecteur, vd1: Vecteur, p2: Vecteur, vd2: Vecteur) -> Vecteur:
    """Renvoie le point d'intersections de deux droites grâce à un de leurs points et leurs vecteurs directeurs."""
    x1, y1 = p1
    x2, y2 = p2
    a1, b1 = vd1
    a2, b2 = vd2
    t = (a2 * (y2 - y1) - b2 * (x2 - x1)) / (a2 * b1 - b2 * a1)
    return x1 + a1 * t, y1 + b1 * t


def courbe_bezier(p1: Vecteur, p2: Vecteur, p3: Vecteur, n: int) -> list[Vecteur]:
    """Renvoie n points de la courbe de Bézier définie par les points de contrôle p1, p2 et p3."""
    points = []
    a1, a2, a3 = np.array(p1), np.array(p2), np.array(p3)
    for i in range(n + 1):
        t = i / n
        a = (1 - t) * (1 - t) * a1 + 2 * (1 - t) * t * a2 + t * t * a3
        points.append(a.tolist())
    return points


def closest_colour(requested_colour: Couleur) -> str:
    """Renvoie le nom de la couleur correspondante."""
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_colour_name(requested_colour: Couleur) -> str:
    """Renvoie le nom de la couleur la plus proche."""
    try:
        closest_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
    return closest_name
