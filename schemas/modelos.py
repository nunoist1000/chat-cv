from pydantic import BaseModel, Field
from datetime import datetime
import pytz


def format_datetime():
    """Devuelve en formato dia-mes-año hora:minuto:segundo
    el momento actual

    Returns
    -------
    _type_
        _description_
    """
    return datetime.strftime(datetime.now(tz=pytz.timezone('Europe/Madrid')),format="%d-%m-%Y %H:%M:%S")

class PreguntasRespuestas(BaseModel):
    id_sesion: str
    query_num: int
    pregunta: str
    respuesta: str
    hora_fecha: datetime = Field(default_factory=format_datetime)
    coste: float
    tokens: int

# Esquema para guardar el numero de descargas del cv
class ContadorCV(BaseModel): 
    fecha_desde: datetime
    contador: int
    fecha_ultimo : datetime = Field(default_factory=datetime.now)
