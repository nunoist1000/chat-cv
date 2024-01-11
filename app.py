from datetime import datetime
from db_client import get_database
from bson import ObjectId
from openai import OpenAI
import os
from pathlib import Path
import pytz
import streamlit as st
import time


CONTADOR_ID = ObjectId('6486283c707ebb023db021e4')
CONTEXT_CV_FOLDER = Path("docs")
CONTEXT_CV_FILE = "descriptif_cv_for_llm.txt"
CONTEXT_CV_PATH = CONTEXT_CV_FOLDER / CONTEXT_CV_FILE
CV_FOLDER = Path("docs")
CV_FILE = "cv.pdf"
CV_PATH = CV_FOLDER / CV_FILE
db_conn = get_database()
format_datetime = datetime.strftime(datetime.now(tz=pytz.timezone('Europe/Madrid')),format="%d-%m-%Y %H:%M:%S")
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

def format_prompt(prompt:str, **kwargs) -> str:
    return prompt.format(**kwargs)

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
        
def get_welcome_msg() -> str:
    msg = f"{custom_saludo()} Mi nombre es {BOT_NAME} 😊.\
                    \nSoy el asistente personal de Sergio y puedo responderte a cualquier pregunta que tengas sobre su curriculum.\
                    \nSi lo deseas también te lo puedes descargar desde la barra lateral izquierda."
    return msg
        
def actualizar_contador()->None:
    """Actualiza el contador de descargas del CV sumando 1 y añadiendo la fecha de la última descarga.
    """
    db_conn["ContadorCV"].update_many(
    {"_id" : CONTADOR_ID}, 
    {"$inc" : {"contador" : 1}, #incrementamos en 1
    "$set":{"fecha_ultimo" : format_datetime}},
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

def get_actual_model() -> str:
    return st.session_state['openai_model']

def update_total_cost(tokens:int) -> float:
    nuevo_coste = tokens * pricing.get(get_actual_model(), 0)
    st.session_state['total_cost'] += nuevo_coste
    return st.session_state['total_cost']

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
    # Set a default model
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = MODELO
    # Inicializamos el precio
    if 'total_cost' not in st.session_state:
        st.session_state['total_cost'] = 0
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
                                #stream=True,
                            )
        for char in response.choices[0].message.content:
            full_response += char
            message_placeholder.markdown(full_response + "▌")
            time.sleep(0.03)
        message_placeholder.markdown(full_response)
        update_total_cost(response.usage.total_tokens)
        st.session_state.messages.append({"role": "assistant", "content": full_response})    

if __name__ == '__main__':
    main()
    st.write(st.session_state.get('total_cost', 0))