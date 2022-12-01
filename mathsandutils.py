import numpy as np
from colorama import Fore
import json
import settings as s


np.seterr("raise")

ids = {-1: None}  # dict des identifiants, initialisé à -1 pour max(id.keys())


def empty(*args, **kwargs): ...


def new_id(obj, obj_id=None):
    """Créer ou ajoute un identifiant à un objet."""
    if obj_id is None:  # si aucun identifiant fourni, prendre celui après le max
        obj_id = max(ids.keys()) + 1
    ids[obj_id] = obj
    return obj_id


def get_by_id(obj_id: int):
    """Renvoie l'objet associé à l'identifiant donné."""
    return ids[obj_id]


def length(point1: (float, float), point2: (float, float)):
    """Longueur point1-point2."""
    x1, y1 = point1
    x2, y2 = point2
    return np.sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))


def vect_dir(start: (float, float), end: (float, float)):
    """Renvoyer le vecteur directeur normé d'une droite."""
    x1, y1 = start
    x2, y2 = end
    a, b = x2 - x1, y2 - y1
    n = norme((a, b))
    return a/n, b/n


def norme(vect: (float, float)):
    """Norme du vecteur."""
    a, b = vect
    return np.sqrt(a*a + b*b)


def vect_norm(vecteur: (float, float), nouv_norme: float = 1):
    """Vecteur normal et normé à un autre vecteur."""
    a, b = vecteur
    coeff = nouv_norme/norme(vecteur)
    return -b*coeff, a*coeff


def vect_angle(vect: (float, float)):
    """Angle du vecteur, en degrés."""
    a, b = vect
    return -np.degrees(np.angle(a+1j*b))


def rec_round(obj, prec: int = None):
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


def log(string: str, level: int = 2):
    """
    Affiche un message.

    :param string: message
    :param level: 0 = essentiel, 1 = erreur, 2 = info, 3 = debug
    """
    if level <= s.LOGGING_LEVEL:
        print([Fore.CYAN, Fore.RED, "", Fore.LIGHTBLACK_EX][level] + string + Fore.RESET)


def parse(string: str):
    """
    String to dict

    :param string: string to parse
    :return: dict
    """
    return json.loads(string.replace("'", '"'))


def update_taylor(car, dt):
    """Calcule les vecteurs du mouvement avec de simples séries de Taylor"""
    car.v = car.v + car.a*dt  # dev de taylor ordre 1
    car.d = car.d + car.v*dt + 1/2*car.a*dt*dt  # dev de taylor ordre 2


def update_taylor_protected(car, dt):
    """Calcule les vecteurs du mouvement avec de simples séries de Taylor, en évitant v < 0"""
    car.v = max(car.v + car.a*dt, 0)  # dev de taylor ordre 1, protégé
    car.d = car.d + max(0, car.v*dt + 1/2*car.a*dt*dt)  # dev de taylor ordre 2


def idm(car, prev_car, dt):
    """Intelligent Driver Model."""

    if prev_car:
        delta_d = prev_car.d - (car.d + car.length)
        delta_v = car.v - prev_car.v
        dd_parfait = s.DD_MIN + max(0, car.v * s.T_REACT + car.v * delta_v / np.sqrt(2 * s.A_MIN * s.A_MAX))
        a_interaction = (dd_parfait/delta_d)**2
    else:
        a_interaction = 0

    car.a = s.A_MAX * (1 - (car.v/s.V_MAX) ** s.A_EXP - a_interaction)

    update_taylor_protected(car, dt)


def intersection_droites(p1, vd1, p2, vd2):
    """Renvoie le point d'intersections de deux droites sachant un de leur point et leur vecteur directeur"""
    x1, y1 = p1
    x2, y2 = p2
    a1, b1 = vd1
    a2, b2 = vd2
    t = (a2*(y2-y1) - b2*(x2-x1))/(a2*b1 - b2*a1)
    return x1 + a1*t, y1 + b1*t


def courbe_bezier(p1, p2, p3, n):
    """Renvoie n points de la courbe de Bézier définie par les points de contrôle p1, p2 et p3"""
    points = []
    a1, a2, a3 = np.array(p1), np.array(p2), np.array(p3)
    for i in range(n + 1):
        t = i/n
        a = (1 - t)*(1 - t) * a1 + 2 * (1 - t) * t * a2 + t * t * a3
        points.append(a.tolist())
    return points
