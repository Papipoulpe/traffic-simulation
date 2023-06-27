import traceback
from typing import *
from numpy.typing import NDArray
import numpy as np
import webcolors

from .settings import simulation_configuration as sc
from .constants import *


np.seterr(all="raise", under="ignore")  # change la gestion des erreurs de maths (division par zéro, racine de négatif...)
npa = np.array  # raccourcis pour les fonctions numpy de base
npz = np.zeros


Coordinates: TypeAlias = NDArray[np.float64]  # définition du type Coordinates = (x, y)
Color: TypeAlias = tuple[int, int, int]  # définition du type Color = (r, g, b)

_sentinel = object()  # sentinel pour get_by_id


def empty_function(*_, **__): ...  # fonction qui à tout associe rien


def new_id(obj, obj_id: int | None = None, pos=False) -> int:
    """Crée et renvoie un identifiant d'objet."""
    if obj_id in sc.dynamic_data["ids"]:  # si l'identifiant est déjà pris, on grogne
        raise ValueError(f"L'identifiant {obj_id} est déjà utilisé.")

    if not sc.dynamic_data["ids"]:  # s'il convient pas, idem
        raise Exception("Vous devez d'abord créer une simulation avant de définir tout autre objet.")

    if obj_id is not None and not (isinstance(obj_id, int) and obj_id > 0):
        raise ValueError(f"Un identifiant doit être un entier strictement positif, pas {obj_id}.")

    if obj_id is None:  # si aucun identifiant fourni
        if pos:  # s'il est demandé que l'identifiant soit positif
            obj_id = max(sc.dynamic_data["ids"].keys()) + 1  # on prend celui après le plus grand
        else:
            obj_id = min(sc.dynamic_data["ids"].keys()) - 1  # sinon, on prend celui avant le plus petit

    sc.dynamic_data["ids"][obj_id] = obj  # on associe l'objet à son identifiant

    return obj_id


def get_by_id(obj_id: int, default=_sentinel) -> Any:
    """Renvoie l'objet associé à l'identifiant donné."""
    return sc.dynamic_data["ids"].get(obj_id, default) if default != _sentinel else sc.dynamic_data["ids"][obj_id]


def norm(v: Coordinates):
    """Renvoie la norme ``||v||``."""
    return np.sqrt(v @ v)


def normed(v: Coordinates, new_norm: float = 1) -> Coordinates:
    """Renvoie ``new_norm * v / ||v||``."""
    return new_norm * v / norm(v)


def distance(p1: Coordinates, p2: Coordinates) -> float:
    """Renvoie la longueur du segment ``[p1p2]``."""
    return norm(p2 - p1)


def direction_vector(p1: Coordinates, p2: Coordinates) -> Coordinates:
    """Renvoie le vecteur directeur normé de la droite ``(p1p2)``."""
    return normed(p2 - p1)


def normal_vector(v: Coordinates, new_norm: float = 1) -> Coordinates:
    """Renvoie un vecteur normal au vecteur ``v``, éventuellement renormé."""
    a, b = v
    return normed(npa((-b, a)), new_norm)


def angle_of_vect(v: Coordinates) -> float:
    """Angle du vecteur ``v`` avec l'axe des abscisses, en degrés."""
    u = npa((1, -1j))
    return np.angle(u @ v, deg=True)


def update_taylor(car, dt: float):
    """Calcule les vecteurs du mouvement de la voiture avec des séries de Taylor, en évitant v < 0.

    Args:
        car: voiture dont la vitesse et la distance doivent être mis à
            jour
        dt: durée du mouvement
    """
    if car.v + car.a * dt < 0:  # si le prochain v est négatif
        car.d -= 1 / 2 * car.v * car.v / car.a
        car.v = 0
    else:
        car.v += car.a * dt  # devéloppent de Taylor à l'ordre 1
        car.d += car.v * dt + 1 / 2 * car.a * dt * dt  # devéloppement de Taylor à l'ordre 2


def idm(car, leader_coords: tuple[float, float] | None) -> float:
    """Calcul l'accélération d'une voiture d'après l'*Intelligent Driver Model*."""
    if leader_coords is not None:  # si on a un leader
        delta_d, lead_v = leader_coords

        delta_v = car.v - lead_v

        desired_delta_d = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(2 * sc.a_min_conf * car.a_max))
        if delta_d == 0:
            delta_d = 1e-4
        a_interaction = (temp := (desired_delta_d / delta_d)) * temp
    else:
        a_interaction = 0

    a_free_road = 1 - np.float_power((car.v / car.v_max), car.a_exp)
    a_idm = car.a_max * (a_free_road - a_interaction)

    return a_idm


def iidm(car, leader_coords: tuple[float, float] | None) -> float:
    """Calcul l'accélération d'une voiture d'après l'*Improved Intelligent Driver Model*."""
    if leader_coords is None:  # si pas de leader
        if car.v <= car.v_max:
            return car.a_max * (1 - (car.v/car.v_max) ** car.a_exp)
        else:
            return - sc.a_min_conf * (1 - np.float_power(car.v_max / car.v, car.a_max * car.a_max / sc.a_min_conf))

    else:
        delta_d, lead_v = leader_coords
        delta_v = car.v - lead_v
        desired_delta_d = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(2 * sc.a_min_conf * car.a_max))
        z = desired_delta_d / delta_d if delta_d > 0 else INF

        if car.v <= car.v_max:
            a_free_road = car.a_max * (1 - (car.v / car.v_max) ** car.a_exp)

            if z >= 1:
                return car.a_max * (1 - z * z)
            else:
                if a_free_road > 0:
                    return a_free_road * (1 - np.float_power(z, 2 * car.a_max / a_free_road))
                else:
                    return 0

        else:
            a_free_road = - sc.a_min_conf * (1 - np.float_power(car.v_max / car.v, car.a_max * car.a_max / sc.a_min_conf))

            if z >= 1:
                return a_free_road + car.a_max * (1 - z * z)
            else:
                return a_free_road


def lines_intersection(p1: Coordinates, vd1: Coordinates, p2: Coordinates, vd2: Coordinates) -> Coordinates:
    """Renvoie le point d'intersections de deux droites grâce à un de leurs points et leurs vecteurs directeurs."""
    x1, y1 = p1
    x2, y2 = p2
    a1, b1 = vd1
    a2, b2 = vd2
    t = (a2 * (y2 - y1) - b2 * (x2 - x1)) / (a2 * b1 - b2 * a1)
    return p1 + vd1 * t


def bezier_curve(p1: Coordinates, p2: Coordinates, p3: Coordinates, n: int) -> list[Coordinates]:
    """Renvoie ``n`` points de la courbe de Bézier définie par les points de contrôle ``p1``, ``p2`` et ``p3``."""
    points = []
    for i in range(n):
        t = i / (n - 1)
        point = (1 - t) * (1 - t) * p1 + 2 * (1 - t) * t * p2 + t * t * p3
        points.append(point)
    return points


def closest_color(requested_color: Color) -> str:
    """Renvoie le nom anglais de la couleur correspondante."""
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_color_name(requested_color: Color) -> str:
    """Renvoie le nom anglais de la couleur la plus proche."""
    try:
        closest_name = webcolors.rgb_to_name(requested_color)
    except ValueError:
        closest_name = closest_color(requested_color)
    return closest_name


def is_inside_circle(m: Coordinates, circle: tuple[Coordinates, float]) -> bool:
    """Renvoie si le point ``m`` appartient au disque, défini par son centre et son rayon."""
    center, radius = circle
    return (m - center) @ (m - center) <= radius*radius


def do_polygons_intersect(polygon1: Sequence[Coordinates], polygon2: Sequence[Coordinates]):
    """Détermine si deux polygones convexes sont d'intersection vide ou non, en utilisant le théorème de séparation des
    polygones convexes.
    """
    for polygon in (polygon1, polygon2):
        # pour chaque polygone, on regarde si une de leurs arêtes les sépare
        n = len(polygon)
        for i in range(n):
            # on prend deux sommets successifs pour regarder une arête
            vertice1 = polygon[i]
            vertice2 = polygon[(i + 1) % n]

            # on prend un vecteur normal à cette arête
            normal = normal_vector(vertice2 - vertice1)

            # on les projette selon ce vecteur normal et on regarde si les segments obtenus s'intersectent
            min_proj_p1 = min(v @ normal for v in polygon1)
            max_proj_p2 = max(v @ normal for v in polygon2)

            if min_proj_p1 >= max_proj_p2:
                return False

            min_proj_p2 = min(v @ normal for v in polygon2)
            max_proj_p1 = max(v @ normal for v in polygon1)

            if min_proj_p2 >= max_proj_p1:
                return False

    # si aucune arête ne sépare les polygones, alors ils s'intersectent
    return True


def red_to_blue_gradient(shade: float):
    """Renvoie une couleur entre bleu et route selon la valeur de ``shade``, avec environ
    0 -> rouge,
    0.25 -> orange,
    0.5 -> jaune,
    0.75 -> vert,
    1 -> bleu.
    """
    return ROGB_GRADIENT[max(min(round(shade * (len(ROGB_GRADIENT) - 1)), len(ROGB_GRADIENT) - 1), 0)]


def tbold(text):
    """Renvoie le texte formatté en gras pour la sortie standard."""
    return TXT_BOLD + str(text) + TXT_RESET


def tred(text):
    """Renvoie le texte formatté en rouge pour la sortie standard."""
    return TXT_RED + str(text) + TXT_RESET


def print_error(exception):
    """Affiche la dernière erreur dans la sortie standard."""
    if sc.print_error:
        print(tred(f"\n*** Erreur : {exception} ***\n\n{traceback.format_exc()}"))


def scale_to_si_unit(attr, val):
    unit = UNITS_OF_ATTR.get(attr, "")

    if "m" in unit and isinstance(val, (int, float)):
        return val / sc.scale

    else:
        return val
