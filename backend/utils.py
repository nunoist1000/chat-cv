"""Script para recoger funciones auxiliares relacionadas con la gestión del backend
"""
from datetime import datetime
import pytz
import random
import string

from backend.paths import CONTEXT_CV_PATH

def format_datetime() -> str:
    """Devuelve en formato dia-mes-año hora:minuto:segundo
    el momento actual

    Returns
    -------
    _type_
        formato del día y hora
    """
    return datetime.strftime(datetime.now(tz=pytz.timezone('Europe/Madrid')),format="%d-%m-%Y %H:%M:%S")

def create_id_session(k:int=4) -> str:
    """Crea un ID de sesión de k letras mayúsculas
    para identificar las mismas sesiones

    Parameters
    ----------
    k : int, optional
        _description_, by default 4

    Returns
    -------
    str
        _description_
    """
    return "".join(random.choices(string.ascii_uppercase,k=k))

def get_context() -> str:
    """Carga el contenido del contexto (mi CV) en un string

    Returns
    -------
    str
        El contexto que usará el LLM para el in-context learning
    """
    if CONTEXT_CV_PATH.exists():
        #al ser objeto Path, se encarga de abrir y cerrar el archivo
        context = CONTEXT_CV_PATH.read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"No se encuentra el ficher {CONTEXT_CV_PATH}")
    return context