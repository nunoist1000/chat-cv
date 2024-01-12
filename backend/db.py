"""Script para recoger toda la lógica relacionada con la base de datos. mongoDB en este caso
"""
import os

from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient

from backend.utils import format_datetime
from backend.schemas.db_schemas import PreguntasRespuestas

load_dotenv()

CONTADOR_ID = ObjectId('6486283c707ebb023db021e4')
DB_CLIENT = MongoClient(os.environ["DB_MONGO"])
DB = DB_CLIENT["CHAT-CV"]


def update_counter() -> None:
    """Actualiza el contador de descargas del CV sumando 1 y añadiendo la fecha de la última descarga.
    """
    DB["ContadorCV"].update_many(
    {"_id" : CONTADOR_ID}, 
    {"$inc" : {"contador" : 1}, # incrementamos en 1
    "$set":{"fecha_ultimo" : format_datetime()}},
    )

def insert_schema_in_db(db_schema:PreguntasRespuestas) -> None:
    """Inserta en base de datos la pregunta y la respuesta asi como la fecha y hora.
    En formato de clase PreguntasRespuestas

    Parameters
    ----------
    db_schema : models.PreguntasRespuestas
        _description_
    """
    DB["PreguntasRespuestas"].insert_one(db_schema.dict())