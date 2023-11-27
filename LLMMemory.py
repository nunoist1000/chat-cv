import streamlit as st
import os
import time
import random

import openai
import requests

from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate

from langchain.chains import (
    create_tagging_chain_pydantic, 
    LLMChain,
    ConversationChain,
)
from langchain.memory import ConversationBufferMemory

from langchain.callbacks import get_openai_callback
from langchain.prompts.chat import (
    SystemMessagePromptTemplate,
    ChatPromptTemplate,
)

from langchain.schema import (
    AIMessage,
    HumanMessage,
    BaseMessage,
    SystemMessage
)
from datetime import datetime
import pytz

from pathlib import Path
import schemas.modelos as models


## CONSTANTES ##
BOT_NAME = "Renardo"
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
CONTEXT_CV_FOLDER = Path("docs")
CONTEXT_CV_FILE = "descriptif_cv_for_llm.txt"
CONTEXT_CV_PATH = CONTEXT_CV_FOLDER / CONTEXT_CV_FILE
SOUND_FOLDER = Path("sounds")
SOUND_FILE = "notification.mp3"
SOUND_PATH = SOUND_FOLDER / SOUND_FILE
ANSWER_ERROR = "Lo siento pero parece que se ha producido un error y no puedo seguir respondiendo... 😌"
TEMPLATE = """
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

llm = ChatOpenAI(
    #model_name="gpt-3.5-turbo-16k",
    model_name="gpt-4",
    #model_name="gpt-3.5-turbo" if st.session_state["total_tokens"] <= 4000 else "gpt-3.5-turbo-16k",
    temperature=0.1,
    openai_api_key=OPENAI_API_KEY,
    #max_tokens=4000, #La version standard tiene 4K, el gpt-3.5-turbo-16k tiene 16K
)
memory = ConversationBufferMemory()
chat = ConversationChain(
    llm=llm,
    memory=memory,
)
llm_extraction = ChatOpenAI(temperature=0, model="gpt-3.5-turbo",openai_api_key=OPENAI_API_KEY)

## FUNCIONES ##
def custom_saludo()->str:
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

def display_audio_unsafe()->None:
    #TODO No consigo que funcione
    "Ejecuta mediante codigo javascript un audio"
    st.markdown(
    f"""
    <audio id="my_audio" src={SOUND_PATH} preload="auto"></audio>
    <script>
    var audio = document.getElementById("my_audio");
    audio.play();
    </script>
    """,
    unsafe_allow_html=True,
)

def get_context()->str:
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
        st.error("Error al cargar el contexto")
        st.stop()
    return context

def get_system_prompt_message()->BaseMessage:
    """Devuelve el system_message_prompt para meterlo en el historial
    de mensajes de la IA o 'memoria'.

    Returns
    -------
    BaseMessage
        _description_
    """
    prompt = PromptTemplate(
    template = TEMPLATE,
    input_variables = ["nombre_bot","context"]
)
    system_message_prompt = SystemMessagePromptTemplate(prompt=prompt)
    contexto = get_context()
    system_message_prompt = system_message_prompt.format(context=contexto,nombre_bot=BOT_NAME)
    return system_message_prompt

def stream_response_assistant(texto:str,cadencia:float=0.02)->None:
    """Streamea la respuesta del LLM como chat message con una cadencia determinada

    Parameters
    ----------
    texto : str
        El texto a streamear
    cadencia : float, optional
        en segundos cuanto espera antes de mostrar la siguiente cadena de texto, by default 0.03
    """

    with st.chat_message("assistant"):
        frase = ""
        output = st.empty()
        for char in texto:
            frase += char
            output.write(frase)
            time.sleep(cadencia)
            output.empty()
        output.write(frase)

def init_memory()->None:
    if st.session_state.get("messages",None) is None:
        st.session_state["messages"] = [
            get_system_prompt_message(),
            AIMessage(content=f"{custom_saludo()} Mi nombre es {BOT_NAME}.\
                    \nSoy el asistente personal de Sergio y puedo responderte a cualquier pregunta que tengas sobre su curriculum.\
                    \nSi lo deseas también te lo puedes descargar desde la barra lateral izquierda."),
            AIMessage(content="Pero primero, ¿Podrías presentarte un poco?")
            ]
        #Streameamos los dos mensajes iniciales con la función stream_response_assistant
        for ai_msg in st.session_state["messages"][1:]:
            stream_response_assistant(ai_msg.content)
            time.sleep(1)

def actualizar_consumos(response:dict)->None:
    total_tokens = response["tokens"]
    coste = response["coste"]
    st.session_state["total_tokens"] = total_tokens
    st.session_state["cost"] = coste

def mostrar_historial_memory()->None:
    for idx,text in enumerate(st.session_state["messages"][1:]):
        if isinstance(text,HumanMessage):
            with st.chat_message("user"):
                st.write(text.content)
        elif isinstance(text,AIMessage):
            with st.chat_message("assistant"):
                st.write(text.content)

def extraer_detalles_usuario(respuesta_usuario:str)->models.DetalleUsuario:
    """Dado una respuesta de texto del usuario, extrae los datos de la clase DetalleUsuario 
    y devuelve la clase..
    Si no encuentra el nombre devuelve string vacío.

    Parameters
    ----------
    respuesta_usuario : str
        texto del que extraer el nombre

    Returns
    -------
    models.DetalleUsuario
        La clase Detalle Usuario.
    """
    chain = create_tagging_chain_pydantic(models.DetalleUsuario,llm_extraction)
    objeto_detalle_usuario:models.DetalleUsuario = chain.run(respuesta_usuario)
    print("[DEBUG]",objeto_detalle_usuario)
    return objeto_detalle_usuario

def chequear_datos_usuario()->list[str]:
    """Retorna una lista de los detalles del usuario que faltan
    por conocer para que la IA pregunte por esos elementos.

    Returns
    -------
    list[str]
        Lista de elementos que faltan por conocer del usuario.
    """
    ask_for = []
    #Chequeamos si hay campos vacíos
    for campo, valor in st.session_state["detalle_usuario"].dict().items():
        if valor in [None,"",0]:
            ask_for.append(f"{campo}")
    return ask_for

def actualizar_detalles_no_nulos(new_details:models.DetalleUsuario)->None:
    """Dado un objeto de DetalleUsuario, actualiza la variable de sesión
    DetalleUsuario con los nuevos datos proporcionados.

    Parameters
    ----------
    new_details : models.DetalleUsuario
        _description_
    """
    non_empty_details = {k:v for k,v in new_details.dict().items() if v not in [None,""]}
    st.session_state["detalle_usuario"]:models.DetalleUsuario = st.session_state["detalle_usuario"].copy(update=non_empty_details)

def preguntar_por_detalle_usuario(ask_for=["nombre","apellidos","empresa","email"])->AIMessage:
    """Devuelve un AIMessage preguntando por el nombre del usuario.

    Returns
    -------
    AIMessage
        _description_
    """

    TEMPLATE = ChatPromptTemplate.from_template( """ 
    Aqui debajo hay una lista sobre varias cosas que debes preguntar al usuario de manera fluida y conversacional.
    Solo debes preguntas una cosa a la vez aunque no obtengas toda la información.
    NO preguntas como una lista!
    No saludes al usuario!
    No digas 'hola' ni nada parecido.

    ### lista 'ask_for' : {ask_for}
    """
    )

    info_chain = LLMChain(llm=llm_extraction, prompt=TEMPLATE)
    return AIMessage(content=info_chain.run(ask_for=ask_for))

def pipeline_extraer_detalle_usuario(texto_usuario:str)->list[str]:
    """Agrupación de las funciones extraer_detalles_usuario y actualizar_detalles_no_nulos asi como
    chequear_datos_usuario.
    Dado el texto del usuario devuelve la lista de los datos que quedan por preguntar

    Parameters
    ----------
    texto_usuario : str
        _description_

    Returns
    -------
    list[str]
        _description_
    """

    objeto_detalles_usuario:models.DetalleUsuario = extraer_detalles_usuario(texto_usuario)
    actualizar_detalles_no_nulos(objeto_detalles_usuario)
    ask_for:list[str] = chequear_datos_usuario()
    return ask_for

def probabilidad_preguntar(num_preguntas)->bool:
    """Genera una probabilidad del 50%

    Returns
    -------
    bool
        _description_
    """
    max_num = max(0, 7 - num_preguntas)  # Esto evitará que max_num sea 0
    numero = random.randint(0, max_num)
    if numero == 0:
        return False
    else:
        return True

@st.cache_data(show_spinner=False)
def get_response_with_memory(question:str)->dict:
    #Metemos la pregunta en el historial
    st.session_state["messages"].append(HumanMessage(content=question))

    #Mostramos el historial
    mostrar_historial_memory()

    #Reproducir aqui un sonido?
    #display_audio_unsafe() #TODO: Conseguir que funcione la reproducción. Chrome me dice 404 Not Found

    #Obtenemos la respuesta de chatGPT
    response = {}
    with get_openai_callback() as cb:
        try:
            AIMessage_response = llm(st.session_state["messages"])
            response["respuesta"] = AIMessage_response.content            
        except openai.error.AuthenticationError as ae:
            response["respuesta"] = ANSWER_ERROR
            st.error(ae)
            st.session_state["last_exception"] = ae
            st.session_state["messages"].append(AIMessage(content=ANSWER_ERROR))
            st.stop()
        except requests.exceptions.RequestException as re:
            response["respuesta"] = ANSWER_ERROR
            st.error(f"Error de conexión: {re}")
            st.session_state["last_exception"] = re
            st.session_state["messages"].append(AIMessage(content=ANSWER_ERROR))
        except TypeError as te:
            response["respuesta"] = ANSWER_ERROR
            st.error(f"Error de tipo de datos al interactuar con la API de OpenAI.")
            st.session_state["last_exception"] = te
            st.session_state["messages"].append(AIMessage(content=ANSWER_ERROR))
        except ValueError as ve:
            response["respuesta"] = ANSWER_ERROR
            st.error(f"Error de valor al interactuar con la API de OpenAI.")
            st.session_state["last_exception"] = ve
            st.session_state["messages"].append(AIMessage(content=ANSWER_ERROR))
        except Exception as exc:
            response["respuesta"] = ANSWER_ERROR
            st.session_state["last_exception"] = exc
            st.session_state["messages"].append(AIMessage(content=ANSWER_ERROR))        
        
        #Streamear la respuesta
        stream_response_assistant(response["respuesta"],0.03)

        #Añadimos la respuesta al historial
        st.session_state["messages"].append(AIMessage_response)
        response["tokens"] = cb.total_tokens
        response["coste"] = round(cb.total_cost,4)

    #!Inutilizo la parte de extraccion de datos, no funciona demasiado bien
    #!en los mensajes subsiguientes no retiene la información que ya tenia... sacarla de db si exsite ?¿
    #Comprobamos si quedan datos por pedir al usuario:
    #if len(chequear_datos_usuario()) > 0:
    #    #Comprobamos lo que queda por preguntar
    #    ask_for = pipeline_extraer_detalle_usuario(question)
    #    if probabilidad_preguntar(st.session_state.get("query_num",0)):
    #    #Sacamos el mensaje de la IA preguntando
    #        ai_message = preguntar_por_detalle_usuario(ask_for)
    #        #Streameamos el mensaje
    #        stream_response_assistant(ai_message.content)
    #        #metemos en el historial
    #        st.session_state["messages"].append(ai_message)

    #Actualizamos en la sesión los valores
    actualizar_consumos(response)
    return response
