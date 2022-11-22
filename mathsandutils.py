import numpy as np
from colorama import Fore
import json


globvar = {}


def empty(*args, **kwargs): ...


def vect_dir(start, end):
    """Renvoyer le vecteur directeur normé d'une droite"""
    x1, y1 = start
    x2, y2 = end
    a, b = x2 - x1, y2 - y1
    n = norme((a, b))
    return a/n, b/n


def norme(vect):
    """Norme du vecteur"""
    a, b = vect
    return np.sqrt(a*a + b*b)


def vect_norm(vecteur, nouv_norme=1):
    """Vecteur normal et normé à un autre vecteur"""
    a, b = vecteur
    coeff = nouv_norme/norme(vecteur)
    return -b*coeff, a*coeff


def angle(vect):
    """Angle du vecteur, en degrés"""
    a, b = vect
    return -np.degrees(np.angle(a+1j*b))


def wc_to_rc(x, y, size):
    """Convertit des coordonnées pygame en coordonnées classiques"""
    return x, size[1] - y


def rc_to_wc(x, y, size):
    """Convertit des coordonnées classiques en coordonnées pygame"""
    return x, size[1] - y


def coord_mvm_apres_dt(car, dt=1/60):
    """
    ACtualise les coordonnées du mouvement d'une voiture.

    :param car: voiture à actualiser
    :param dt: durée du mouvement
    """
    d, v, a = car.d, car.v, car.a
    d = d + v*dt + 1/2*a*dt*dt  # dev de taylor ordre 2
    v = v + a*dt  # dev de taylor ordre 1
    car.d, car.v, car.a = d, v, a


def rec_round(obj, prec=None):
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
    Affiche un message
    :param string: message
    :param level: 0 = essentiel, 1 = erreur, 2 = info, 3 = debug
    """
    if level <= globvar["logging_level"]:
        print([Fore.CYAN, Fore.RED, "", Fore.LIGHTBLACK_EX][level] + string + Fore.RESET)


def parse(string):
    """
    String to dict

    :param string: string to parse
    :return: dict
    """
    return json.loads(string.replace("'", '"'))
