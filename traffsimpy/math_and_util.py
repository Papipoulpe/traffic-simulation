import json
from typing import *
from numpy.typing import NDArray
import numpy as np
import webcolors

import traffsimpy.settings as s
from .constants import *


np.seterr(all="raise", under="ignore")  # change la gestion des erreurs de maths (division par zéro, racine de négatif...)
npa = np.array  # raccourcis pour les fonctions numpy de base
npz = np.zeros

ids = {}  # dictionnaire des identifiants d'objet

Vecteur: TypeAlias = NDArray[np.float64]  # définiton du type Vecteur = (x, y)
Couleur: TypeAlias = tuple[int, int, int]  # définiton du type Couleur = (r, g, b)


def empty_function(*_, **__): ...  # fonction qui à tout associe rien


def new_id(obj, obj_id: Optional[int] = None, pos: bool = False) -> int:
    """Créer un identifiant d'objet."""
    if obj_id is None:
        if pos:  # si aucun identifiant fourni
            obj_id = max(ids.keys()) + 1
        else:
            obj_id = min(ids.keys()) - 1
    elif obj_id in ids:  # s'il est déjà pris, on grogne
        raise ValueError(f"L'identifiant {obj_id} est déjà utilisé.")
    elif not isinstance(obj_id, int) or obj_id < 0:  # s'il convient pas, idem
        raise ValueError(f"Un identifiant doit être un entier positif, pas {obj_id}.")
    ids[obj_id] = obj  # on associe l'objet à son identifiant
    return obj_id


def get_by_id(obj_id: int) -> Any:
    """Renvoie l'objet associé à l'identifiant donné."""
    return ids[obj_id]


def norm(v: Vecteur):
    """Renvoie la norme ``||v||``."""
    return np.sqrt(v @ v)


def normed(v: Vecteur, new_norm: float = 1) -> Vecteur:
    """Renvoie ``new_norm * v / ||v||``."""
    return new_norm * v / norm(v)


def distance(p1: Vecteur, p2: Vecteur) -> float:
    """Renvoie la longueur du segment ``[p1p2]``."""
    return norm(p2 - p1)


def direction_vector(p1: Vecteur, p2: Vecteur) -> Vecteur:
    """Renvoie le vecteur directeur normé de la droite ``(p1p2)``."""
    return normed(p2 - p1)


def normal_vector(v: Vecteur, new_norm: float = 1) -> Vecteur:
    """Vecteur normal au vecteur ``v``, éventuellement renormé."""
    a, b = v
    return normed(npa((-b, a)), new_norm)


def angle_of_vect(v: Vecteur) -> float:
    """Angle du vecteur ``v`` avec l'axe des abscisses, en degrés."""
    u = npa((1, -1j))
    return np.angle(u @ v, deg=True)


def rec_round(obj: Iterable | float, prec: Optional[int] = None) -> Iterable | float:
    """Arrondi récursif."""
    if isinstance(obj, float):
        return round(obj, prec)
    else:
        res = []
        for e in obj:
            res.append(rec_round(e, prec))
        if isinstance(obj, tuple):
            res = tuple(res)
        return res


def parse(string: str) -> dict:
    """Chaîne de caractères -> dictionnaire."""
    return json.loads(string.replace("'", '"'))


def update_taylor(car, dt: float):
    """
    Calcule les vecteurs du mouvement de la voiture avec des séries de Taylor, en évitant v < 0.

    :param car: voiture dont la vitesse et la distance doivent être mis à jour
    :param dt: durée du mouvement
    """
    if car.v + car.a * dt < 0:  # si le prochain v est négatif
        car.d -= 1 / 2 * car.v * car.v / car.a
        car.v = 0
    else:
        car.v += car.a * dt  # dev de taylor ordre 1
        car.d += car.v * dt + 1 / 2 * car.a * dt * dt  # dev de taylor ordre 2


def idm(car, leader_coords: Optional[Vecteur]) -> float:
    """Calcul l'accélération d'une voiture d'après l'*Intelligent Driver Model*."""
    if leader_coords is not None:  # si on a un leader
        delta_d, lead_v = leader_coords

        delta_v = car.v - lead_v

        dd_parfait = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(2 * s.A_MIN_CONF * car.a_max))
        a_interaction = (temp := (dd_parfait / delta_d)) * temp
    else:
        a_interaction = 0

    a_free_road = 1 - np.float_power((car.v / car.v_max), car.a_exp)
    a_idm = car.a_max * (a_free_road - a_interaction)

    return a_idm


def iidm(car, leader_coords: Optional[Vecteur]) -> float:
    """Calcul l'accélération d'une voiture d'après l'*Improved Intelligent Driver Model*."""
    if car.v <= car.v_max:
        a_free_road = car.a_max * (1 - (car.v/car.v_max) ** car.a_exp)

        if leader_coords is None:
            a_iidm = a_free_road
        else:
            delta_d, lead_v = leader_coords
            delta_v = car.v - lead_v
            dd_parfait = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(2 * s.A_MIN_CONF * car.a_max))
            z = dd_parfait/delta_d if delta_d > 0 else INF

            if z >= 1:
                a_iidm = car.a_max * (1 - z*z)
            else:
                if a_free_road > 0:
                    a_iidm = a_free_road * (1 - np.float_power(z, 2 * car.a_max / a_free_road))
                else:
                    a_iidm = 0

    else:
        a_free_road = - s.A_MIN_CONF * (1 - np.float_power(car.v_max/car.v, car.a_max * car.a_max / s.A_MIN_CONF))

        if leader_coords is None:
            a_iidm = a_free_road
        else:
            delta_d, lead_v = leader_coords
            delta_v = car.v - lead_v
            dd_parfait = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(2 * s.A_MIN_CONF * car.a_max))
            z = dd_parfait/delta_d if delta_d > 0 else INF

            if z >= 1:
                a_iidm = a_free_road + car.a_max * (1 - z*z)
            else:
                a_iidm = a_free_road

    return a_iidm


def lines_intersection(p1: Vecteur, vd1: Vecteur, p2: Vecteur, vd2: Vecteur) -> Vecteur:
    """Renvoie le point d'intersections de deux droites grâce à un de leurs points et leurs vecteurs directeurs."""
    x1, y1 = p1
    x2, y2 = p2
    a1, b1 = vd1
    a2, b2 = vd2
    t = (a2 * (y2 - y1) - b2 * (x2 - x1)) / (a2 * b1 - b2 * a1)
    return p1 + vd1 * t


def bezier_curve(p1: Vecteur, p2: Vecteur, p3: Vecteur, n: int) -> list[Vecteur]:
    """Renvoie ``n`` points de la courbe de Bézier définie par les points de contrôle ``p1``, ``p2`` et ``p3``."""
    points = []
    for i in range(n):
        t = i / (n - 1)
        point = (1 - t) * (1 - t) * p1 + 2 * (1 - t) * t * p2 + t * t * p3
        points.append(point)
    return points


def closest_color(requested_color: Couleur) -> str:
    """Renvoie le nom anglais de la couleur correspondante."""
    min_colours = {}
    for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_color[0]) ** 2
        gd = (g_c - requested_color[1]) ** 2
        bd = (b_c - requested_color[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]


def get_color_name(requested_color: Couleur) -> str:
    """Renvoie le nom anglais de la couleur la plus proche."""
    try:
        closest_name = webcolors.rgb_to_name(requested_color)
    except ValueError:
        closest_name = closest_color(requested_color)
    return closest_name


def is_inside_rectangle(m: Vecteur, rectangle: np.ndarray) -> bool:
    """Renvoie si le point ``m`` est à l'intérieur du rectangle, défini par ses quatres sommets."""
    a, b, c, d = rectangle
    am = m - a
    ab = b - a
    ad = d - a
    # M est dans ABCD ssi (0 < AM⋅AB < AB⋅AB) et (0 < AM⋅AD < AD⋅AD)
    return 0 <= am @ ab <= ab @ ab and 0 <= am @ ad <= ad @ ad


def is_inside_circle(m: Vecteur, circle: tuple[Vecteur, float]) -> bool:
    """Renvoie si le point ``m`` appartient au disque, défini par son centre et son rayon."""
    center, radius = circle
    return (m - center) @ (m - center) <= radius*radius


def blue_red_gradient(shade: float):
    return s.ROGB_GRADIENT[max(min(round(shade * (len(s.ROGB_GRADIENT) - 1)), len(s.ROGB_GRADIENT) - 1), 0)]


def tbold(text):
    """Renvoie le texte formatté en gras pour la sortie standard."""
    return TXT_BOLD + str(text) + TXT_RESET


def tred(text):
    """Renvoie le texte formatté en rouge pour la sortie standard."""
    return TXT_RED + str(text) + TXT_RESET
