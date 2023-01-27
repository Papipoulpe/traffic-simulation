import json
from typing import *
from numpy.typing import NDArray
import numpy as np
import pandas as pd
import webcolors

import traffsimpy.settings as s
from .constants import *


np.seterr("raise")  # change la gestion des erreurs de maths (division par zéro, racine de réel négatif...)

ids = {}  # dictionnaire des identifiants d'objet

Vecteur: TypeAlias = NDArray[np.float64]  # définiton du type Vecteur = (a, b)
Couleur: TypeAlias = tuple[int, int, int]  # définiton du type Couleur = (r, g, b)


def empty_function(*_, **__): ...  # fonction qui à tout associe rien


def new_id(obj, obj_id: Optional[int] = None) -> int:
    """Créer un identifiant d'objet."""
    if obj_id is None:  # si aucun identifiant fourni, prendre celui après le max
        obj_id = max(ids.keys()) + 1
    ids[obj_id] = obj
    return obj_id


def get_by_id(obj_id: int) -> Any:
    """Renvoie l'objet associé à l'identifiant donné."""
    return ids[obj_id]


npa = np.array
npz = np.zeros


def norm(v: Vecteur):
    """Renvoie la norme ``||v||``."""
    return np.sqrt(v @ v)


def normed(v: Vecteur, new_norm: float = 1) -> Vecteur:
    """Renvoie ``new_norm * v / ||v||``."""
    return new_norm * v / norm(v)


def length(p1: Vecteur, p2: Vecteur):
    """Renvoie la longueur du segment ``[p1p2]``."""
    return norm(p2 - p1)


def direction_vector(p1: Vecteur, p2: Vecteur) -> Vecteur:
    """Renvoie le vecteur directeur normé de la droite ``(p1p2)``."""
    return normed(p2 - p1)


def normal_vector(v: Vecteur, new_norm: float = 1) -> Vecteur:
    """Vecteur normal au vecteur ``v``, éventuellement renormé."""
    a, b = v
    return normed(npa((-b, a)), new_norm)


def angle_of_vect(v: Vecteur):
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
    """Calcule les vecteurs du mouvement avec des séries de Taylor"""
    car.v = car.v + car.a * dt  # dev de taylor ordre 1
    car.d = car.d + car.v * dt + 1 / 2 * car.a * dt * dt  # dev de taylor ordre 2


def update_taylor_protected(car, dt: float):
    """Calcule les vecteurs du mouvement avec des séries de Taylor, en évitant v < 0"""
    car.v = max(car.v + car.a * dt, 0)  # dev de taylor ordre 1, protégé
    car.d = car.d + max(0, car.v * dt + 1 / 2 * car.a * dt * dt)  # dev de taylor ordre 2, protégé


def idm(car, leader_coords: Optional[Vecteur], dt: float):
    """Intelligent Driver Model. Calcule l'accélération idéale de la voiture."""
    if leader_coords is not None:  # si on a un leader
        delta_d, lead_v = leader_coords

        if delta_d <= 0:  # si la voiture est en avance, la faire attendre et ralentir
            car.d, car.v, car.a = car.d, 0, car.a
            return

        delta_v = car.v - lead_v

        dd_parfait = car.delta_d_min + max(0, car.v * car.t_react + car.v * delta_v / np.sqrt(
            2 * s.A_MIN_CONF * car.a_max))
        a_interaction = (dd_parfait / delta_d) ** 2
    else:
        a_interaction = 0

    a_free_road = 1 - (car.v / car.road.v_max) ** car.a_exp
    a_idm = car.a_max * (a_free_road - a_interaction)
    car.a = min(car.a_min, a_idm)

    update_taylor_protected(car, dt)


def intersection_droites(p1: Vecteur, vd1: Vecteur, p2: Vecteur, vd2: Vecteur) -> Vecteur:
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
    for i in range(n + 1):
        t = i / n
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


def is_inside_circle(m: Vecteur, circle: tuple[Vecteur, float]):
    """Renvoie si le point ``m`` appartient au disque, défini par son centre et son rayon."""
    center, radius = circle
    return (m - center) @ (m - center) <= radius*radius


def data_frame(columns: list[str], data: Any = None) -> pd.DataFrame:
    """Renvoie une table de données."""
    return pd.DataFrame(data=data, columns=columns)


def blue_red_gradient(shade: float):
    return s.ROGB_GRADIENT[max(min(round(shade * (len(s.ROGB_GRADIENT) - 1)), len(s.ROGB_GRADIENT) - 1), 0)]


def tbold(text):
    """Renvoie le texte formatté en gras pour la sortie standard."""
    return TXT_BOLD + str(text) + TXT_RESET


def tred(text):
    """Renvoie le texte formatté en rouge pour la sortie standard."""
    return TXT_RED + str(text) + TXT_RESET
