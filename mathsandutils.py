import numpy as np
from colorama import Fore
import json
import settings as s


def empty(*args, **kwargs): ...


def length(point1, point2):
    """Longueur point1-point2."""
    x1, y1 = point1
    x2, y2 = point2
    return np.sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))


def vect_dir(start, end):
    """Renvoyer le vecteur directeur normé d'une droite."""
    x1, y1 = start
    x2, y2 = end
    a, b = x2 - x1, y2 - y1
    n = norme((a, b))
    return a/n, b/n


def norme(vect):
    """Norme du vecteur."""
    a, b = vect
    return np.sqrt(a*a + b*b)


def vect_norm(vecteur, nouv_norme=1):
    """Vecteur normal et normé à un autre vecteur."""
    a, b = vecteur
    coeff = nouv_norme/norme(vecteur)
    return -b*coeff, a*coeff


def vect_angle(vect):
    """Angle du vecteur, en degrés."""
    a, b = vect
    return -np.degrees(np.angle(a+1j*b))


def wc_to_rc(x, y, size):
    """Convertit des coordonnées pygame en coordonnées classiques."""
    return x, size[1] - y


def rc_to_wc(x, y, size):
    """Convertit des coordonnées classiques en coordonnées pygame."""
    return x, size[1] - y


def rec_round(obj, prec=None):
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


def parse(string):
    """
    String to dict

    :param string: string to parse
    :return: dict
    """
    return json.loads(string.replace("'", '"'))


def update_taylor(d, v, a, dt):
    """Calcule les vecteurs du mouvement avec de simples séries de Taylor"""
    v = v + a*dt  # dev de taylor ordre 1
    d = d + v*dt + 1/2*a*dt*dt  # dev de taylor ordre 2
    return d, v, a


def update_taylor_protected(d, v, a, dt):
    """Calcule les vecteurs du mouvement avec de simples séries de Taylor, en évitant v < 0"""
    v = max(v + a*dt, 0)  # dev de taylor ordre 1, protégé
    d = d + v*dt + 1/2*a*dt*dt  # dev de taylor ordre 2
    return d, v, a


def idm(d, v, dd, dv, dt):
    """Intelligent Driver Model."""

    dd_parfait = s.DD_MIN + max(0, v*s.T_REACT + v * dv / np.sqrt(2 * s.A_MIN * s.A_MAX))

    a = s.A_MAX * (1 - (v/s.V_MAX)**s.A_EXP - (dd_parfait/dd)**2)

    return update_taylor_protected(d, v, a, dt)


def arc_type(start, end, sens):
    sx, sy = start
    ex, ey = end
    if ex > sx:
        if ey > sy:
            returning = "hd"
        else:
            returning = "bd"
    else:
        if ey > sy:
            returning = "hg"
        else:
            returning = "bg"
    return returning + sens
