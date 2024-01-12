"""Script con todo el código relacionado con le chat Bot
"""
from datetime import datetime
import pytz

from backend.utils import get_context

MODELO = "gpt-3.5-turbo-1106"
BOT_NAME = 'Renardo'
PROMPT = """
Vamos a pensar paso a paso.
Eres un asistente muy útil, simpático y educado especializado en proporcionar información sobre Sergio.
Tu nombres es {nombre_bot}.
Tus objetivos son:
- Proporcionar información clara y concisa sobre el CV de Sergio cogida del contexto proporcionado.
NO saludes al usuario.
Puedes expresar de otro modo las frases del contexto.
Intenta siempre responder a la pregunta de manera amable.
Responde en el mismo idioma que el usuario.
Recuerda al usuario de vez en cuando que puede descargarse el CV de Sergio desde la barra lateral izquierda.
Recuerda que eres un asistente especializado en responder sobre la vida y la carrera de Sergio.
Recuerda que eres también un amable chatbot teniendo una conversación con un humano y respondiendo sus preguntas en base al contexto.
Utiliza el nombre del usuario en tus respuestas.
NO uses el apellido del usuario. NO uses el nombre completo del usuario, usa sólo su nombre.

% CONTEXTO
{context}
"""
pricing = {
    "gpt-3.5-turbo-1106": 0.0020e-3, # 16K de contexto
    "gpt-3.5-turbo-instruct": 0.0020e-3, # 4K de contexto
    "gpt-4-32k": 0.12e-3, # 32K de contexto
    "gpt-4": 0.06e-3, 
}


def format_prompt(prompt:str, **kwargs) -> str:
    return prompt.format(**kwargs)

def custom_saludo() -> str:
    """Función que devuelve un saludo en función de la hora del día que sea

    Parameters
    ----------
    time : datetime
        datetime.datetime.now()

    Returns
    -------
    str
        Devuelve el saludo personalizado
    """
    time = datetime.now(tz=pytz.timezone('Europe/Madrid'))

    hora_del_dia = time.hour
    SALUDO = {
        range(0,7) : "¡Buenas noches! ",
        range(7,14) : "¡Buenos días! ",
        range(14,17) : "¡Muy buenas! ",
        range(17,20) : "¡Buenas tardes! ",
        range(20,24) : "¡Buenas noches! ",
        }
    
    for hora in SALUDO.keys():
        if hora_del_dia in hora:
            return SALUDO[hora]
        
def get_welcome_msg() -> str:
    msg = f"{custom_saludo()} Mi nombre es {BOT_NAME} 😊.\
                    \nSoy el asistente personal de Sergio y puedo responderte a cualquier pregunta que tengas sobre su curriculum.\
                    \nSi lo deseas también te lo puedes descargar desde la barra lateral izquierda."
    return msg

def calculate_cost(tokens:int, model:str) -> float:
    """Calcula el coste de los tokens en función del modelo

    Parameters
    ----------
    tokens : int
        _description_

    Returns
    -------
    float
        total_cost
    """
    return tokens * pricing.get(model, 0)

def build_system_prompt() -> str:
    """Devuelve el system prompt en str

    Returns
    -------
    str
        _description_
    """
    return format_prompt(PROMPT, context=get_context(), nombre_bot=BOT_NAME)

def get_model() -> str:
    """Devuelve el modelo de openAI

    Returns
    -------
    str
        _description_
    """
    return MODELO