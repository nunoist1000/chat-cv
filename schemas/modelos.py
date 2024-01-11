from pydantic import BaseModel, Field
from datetime import datetime
from bson import ObjectId
import pytz


def format_datetime():
    return datetime.strftime(datetime.now(tz=pytz.timezone('Europe/Madrid')),format="%d-%m-%Y %H:%M:%S")

class PreguntasRespuestas(BaseModel):
    id_sesion: str
    query_num: int
    nombre: str
    apellidos: str
    empresa: str
    email: str
    pregunta: str
    respuesta: str
    hora_fecha: datetime = Field(default_factory=format_datetime)
    coste: float
    tokens: int

class ContadorCV(BaseModel): #Esquema para guardar el numero de descargas del cv
    fecha_desde: datetime
    contador: int
    fecha_ultimo : datetime = Field(default_factory=datetime.now)

class DetalleUsuario(BaseModel):
    nombre: str = Field(
        ...,
        description="El nombre del usuario que chatea con el asistente y hace preguntas sobre el CV de Sergio",
        #exclude=["Sergio","Sergio Tejedor","Sergio Tejedor Moreno"]
            )
    apellidos: str = Field(
        ...,
        description="El o los apellidos del usuario que chatea con el asistente."
    )
    empresa: str = Field(
        ...,
        description="Empresa en la que trabaja actualmente el usuario"
    )
    email: str = Field(
        ...,
        description="El email del usuario que chatea con el asistente."
    )
