
"""Script que recoge el código del frontend con Streamlit
"""
import os
import time
from typing import Union

from openai import OpenAI
import streamlit as st

from backend.db import update_counter, insert_schema_in_db
from backend.schemas.db_schemas import PreguntasRespuestas
from backend.utils import create_id_session
from backend.paths import CV_PATH, CV_FILE
from backend.bot import (build_system_prompt, 
                        get_welcome_msg, 
                        calculate_cost,
                        get_model,
                        get_end_of_conversation,
                        )

STREAM_DELAY = 0.03
FINAL_MSG = '💤...😴...💤'
QUERY_LIMIT = 10

def get_key_sesion(key:str) -> str:
    """Devuelve el valor de una key determinada de la sesión

    Returns
    -------
    str
        el valor de la key de sesión
    """
    return st.session_state[key]

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

def main():
    """Función con el frontend principal"""
    # Cargamos variables del sistema
    st.set_page_config(
    page_title="CV STM",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="auto",
    )
    # Barra lateral con posibilidad de descargar el CV y mi logo personal
    with st.sidebar:
        st.image("img/Logo STM.png")
        st.markdown("""
        <h1 style='text-align: center; color: #292e48; font-family: "Arial", sans-serif;'>
            STM
        </h1>
        """, unsafe_allow_html=True)    
        with open(CV_PATH,"rb") as file:
            st.download_button(
                label = "Descargar",
                data = file,
                file_name = CV_FILE,
                mime = "cv/pdf",
                on_click=update_counter,
                use_container_width=True,
                help="Descarga el CV de STM en formato pdf"
            )
    # Instanciamos cliente OpenAI
    client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Inicializamos todas las variables de sesión
    # Inicializamos una id de sesión
    if st.session_state.get('id_session') is None:
        st.session_state['id_session'] = create_id_session()
    if st.session_state.get('query_num') is None:
        st.session_state['query_num'] = 0
    # Inicializa el modelo
    if st.session_state.get('openai_model') is None:
        st.session_state["openai_model"] = get_model()
    # Inicializamos el precio
    if st.session_state.get('total_cost') is None:
        st.session_state['total_cost'] = 0
    # Inicializamos los tokens totales
    if st.session_state.get('total_tokens') is None:
        st.session_state['total_tokens'] = 0
    # Inicializa el mensaje de bienvenida
    if st.session_state.get('messages') is None:
        st.session_state.messages = []
        # Prompt system
        st.session_state.messages.append(
            {"role": "system", 
                "content": build_system_prompt()
                })
        # Mensaje de bienvenida
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
        for msg in get_welcome_msg():
            full_response += msg
            message_placeholder.markdown(full_response + "▌")
            time.sleep(STREAM_DELAY)
        st.session_state.messages.append({"role": "assistant", "content": get_welcome_msg()})
        st.rerun()

    # Muestra el historial de mensajes menos el system prompt
    for message in st.session_state.messages:
        if message['role'] != 'system':
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input del usuario
    if prompt := st.chat_input("Escribe lo que quieras"):
        # Incrementamos la query
        inc_value_in_session('query_num', 1)
        # Añade el input al historial
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Muestra el mensaje del usuario
        with st.chat_message("user"):
            st.markdown(prompt)
        # Muestra la respuesta del bot en forma de stream
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
        # Comprobar aqui si el número de inputs supera un cierto número
        if (num_query:=st.session_state.get('query_num')) == QUERY_LIMIT:
            text_response = get_end_of_conversation()
        elif num_query > QUERY_LIMIT:
            text_response = FINAL_MSG
        else:
            response = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                    )
            text_response = response.choices[0].message.content
            # Recogemos los tokens
            total_tokens = response.usage.total_tokens
            # Recogemos el coste
            cost = calculate_cost(total_tokens, get_key_sesion('openai_model'))
            # Acumulamos coste total, tokens y la query en sesión
            inc_value_in_session('total_cost', cost)            
            inc_value_in_session('total_tokens', total_tokens)            
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

        for char in text_response:
            full_response += char
            message_placeholder.markdown(full_response + "▌")
            time.sleep(STREAM_DELAY)
        message_placeholder.markdown(full_response)
        # Actualizamos mensaje en sesión para la "memoria"
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        
        

if __name__ == '__main__':
    main()
    #st.session_state