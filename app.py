
from datetime import datetime
import os
from pathlib import Path
import random
import string
import time
from typing import Union

from bson import ObjectId
from openai import OpenAI
import pytz
import streamlit as st

from db_client import get_database
from schemas.modelos import format_datetime, PreguntasRespuestas


CONTADOR_ID = ObjectId('6486283c707ebb023db021e4')
CONTEXT_CV_FOLDER = Path("docs")
CONTEXT_CV_FILE = "descriptif_cv_for_llm.txt"
CONTEXT_CV_PATH = CONTEXT_CV_FOLDER / CONTEXT_CV_FILE
CV_FOLDER = Path("docs")
CV_FILE = "cv.pdf"
CV_PATH = CV_FOLDER / CV_FILE
db_conn = get_database()
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
    "gpt-3.5-turbo-1106": 0.0020e-3,
}

def create_id_session() -> str:
    return "".join(random.choices(string.ascii_uppercase,k=4))

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
        
def actualizar_contador() -> None:
    """Actualiza el contador de descargas del CV sumando 1 y añadiendo la fecha de la última descarga.
    """
    db_conn["ContadorCV"].update_many(
    {"_id" : CONTADOR_ID}, 
    {"$inc" : {"contador" : 1}, #incrementamos en 1
    "$set":{"fecha_ultimo" : format_datetime()}},
    )

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

def get_key_sesion(key:str) -> str:
    """Devuelve una key determinada de la sesión

    Returns
    -------
    str
        el valor de la key de sesión
    """
    return st.session_state[key]

def calculate_cost(tokens:int) -> float:
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
    return tokens * pricing.get(get_key_sesion('openai_model'), 0)

def inc_value_in_session(key:str, value:Union[float, int]) -> float:
    """Incrementa el valor de una variable de la sesión en un determinado valor

    Parameters
    ----------
    cost : float
        _description_

    Returns
    -------
    float
        _description_
    """
    st.session_state[key] += value
    return st.session_state[key]

def insert_schema_in_db(db_schema:PreguntasRespuestas) -> None:
    """Inserta en base de datos la pregunta y la respuesta asi como la fecha y hora.
    En formato de clase PreguntasRespuestas

    Parameters
    ----------
    db_schema : models.PreguntasRespuestas
        _description_
    """
    db_conn["PreguntasRespuestas"].insert_one(db_schema.dict())

def main():
    # Cargamos variables del sistema
    st.set_page_config(
    page_title="CV STM",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="auto",
    )
    #Descargar el CV en pdf en la sidebar
    with st.sidebar:
        st.image("img/Logo STM.png")
        st.markdown("""
        <h1 style='text-align: center; color: #292e48; font-family: "Arial", sans-serif;'>
            STM
        </h1>
        """, unsafe_allow_html=True)    
        with open(CV_PATH,"rb") as file:
            boton = st.download_button(
                label = "Descargar",
                data = file,
                file_name = CV_FILE,
                mime = "cv/pdf",
                on_click=actualizar_contador,#mandar_email("Alguien se ha descargado tu CV en pdf",subject = "Descarga del CV en pdf"),
                use_container_width=True,
                help="Descarga el CV de STM en formato pdf"
            )
    # Set OpenAI API key from Streamlit secrets
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Inicializamos una id de sesión
    if "id_session" not in st.session_state:
        st.session_state['id_session'] = create_id_session()
    if 'query_num' not in st.session_state:
        st.session_state['query_num'] = 0
    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = MODELO
    # Inicializamos el precio
    if 'total_cost' not in st.session_state:
        st.session_state['total_cost'] = 0
    # Inicializamos los tokens totales
    if 'total_tokens' not in st.session_state:
        st.session_state['total_tokens'] = 0
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Prompt system
        st.session_state.messages.append(
            {"role": "system", 
                "content": format_prompt(PROMPT, context=get_context(), nombre_bot=BOT_NAME)
                })
        # Mensaje de bienvenida
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
        for msg in get_welcome_msg():
            full_response += msg
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.02)
        st.session_state.messages.append({"role": "assistant", "content": get_welcome_msg()})
        st.rerun()
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        if message['role'] != 'system':
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    # Accept user input
    if prompt := st.chat_input("Escribe lo que quieras"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
        response = client.chat.completions.create(
                                model=st.session_state["openai_model"],
                                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                            )
        text_response = response.choices[0].message.content
        for char in text_response:
            full_response += char
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.03)
        message_placeholder.markdown(full_response)
        # Recogemos los tokens
        total_tokens = response.usage.total_tokens
        # Recogemos el coste
        cost = calculate_cost(total_tokens)
        # Acumulamos coste total en sesión, tokens y la query
        inc_value_in_session('total_cost', cost)
        inc_value_in_session('query_num', 1)
        inc_value_in_session('total_tokens', total_tokens)
        # Actualizamos mensaje en sesión para la "memoria"
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        # Registramos en base de datos
        schema = PreguntasRespuestas(
            pregunta=prompt,
            id_sesion=get_key_sesion('id_session'),
            query_num=get_key_sesion('query_num'),
            respuesta=text_response,
            coste=cost,
            tokens=total_tokens,
        )
        insert_schema_in_db(schema)
        

if __name__ == '__main__':
    main()
    st.write(st.session_state.get('total_cost', 0), st.session_state.get('total_tokens'))