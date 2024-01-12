from pydantic import BaseModel, Field
from datetime import datetime

from backend.utils import format_datetime

class PreguntasRespuestas(BaseModel):
    """Esquema para insertar en base de datos
    cada query/respuesta del modelo

    Parameters
    ----------
    BaseModel : _type_
        _description_
    """
    id_sesion: str
    query_num: int
    pregunta: str
    respuesta: str
    hora_fecha: datetime = Field(default_factory=format_datetime)
    coste: float
    tokens: int

# Esquema para guardar el numero de descargas del cv
class ContadorCV(BaseModel): 
    """Esquema para ingresar en base de datos
    un trackeo del número de veces que se descarga mi CV

    Parameters
    ----------
    BaseModel : _type_
        _description_
    """
    fecha_desde: datetime
    contador: int
    fecha_ultimo : datetime = Field(default_factory=datetime.now)
