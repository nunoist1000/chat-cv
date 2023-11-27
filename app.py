import streamlit as st
import os
import yagmail
from datetime import datetime
import db_client as db
import schemas.modelos as models
from bson import ObjectId
import string, random
import pytz
import pymongo
from pathlib import Path


## CONFIGURACIÓN ##
st.set_page_config(
    page_title="CV STM",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="auto",
)

## PARAMETROS ##
CV_FOLDER = Path("docs")
CV_FILE = "cv.pdf"
CV_PATH = CV_FOLDER / CV_FILE

GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
YAG = yagmail.SMTP("tejedor.moreno.dev@gmail.com",GOOGLE_API_KEY)
format_datetime = datetime.strftime(datetime.now(tz=pytz.timezone('Europe/Madrid')),format="%d-%m-%Y %H:%M:%S")
format_day = datetime.strftime(datetime.now(tz=pytz.timezone('Europe/Madrid')),format="%d-%m-%Y")
TIME_STAMP = f"[{format_datetime}]"
LOG_FILE = f"qa_log_file[{format_day}].txt"
LOG_FOLDER = Path("logs")
LOG_PATH = LOG_FOLDER / LOG_FILE

db_conn = db.get_database()
CONTADOR_ID = ObjectId('6486283c707ebb023db021e4')

## FUNCIONES ##
def init_variables_sesion()->None:
    if st.session_state.get("total_tokens",None) is None:
        st.session_state["total_tokens"] = 0
    if st.session_state.get("cost",None) is None:
        st.session_state["cost"] = 0
    if st.session_state.get("detalle_usuario",None) is None:
        st.session_state["detalle_usuario"] = models.DetalleUsuario(nombre="",
                                                                    apellidos="",
                                                                    empresa="",
                                                                    email="",
        )

def mandar_email(pregunta:str,response:dict,*,subject:str)->None:
    """Función para enviar por email con yagmail el historial de mensajes
    y los consumos de tokens

    Parameters
    ----------
    email : str
        el email del receptor
    text : str
        El body del email
    """

    text = st.session_state.get("text_HTML","")
    text += f"""<b>Pregunta:</b> {pregunta}\n<b>Respuesta:</b> {response["answer"]}\n<b>Coste acumulado:</b> ${st.session_state["cost"]}\n\n"""
    st.session_state["text_HTML"] = text  

    YAG.send(
    to="tejedor.moreno@gmail.com",
    subject=subject,
    contents=text, 
    #attachments=filename,
)

def log_to_file(pregunta:str,response:dict)->None:
    #raw_text = st.session_state.get("raw_text","")
    raw_text = f"""{TIME_STAMP}\nPregunta: {pregunta}\nRespuesta: {response["respuesta"]}\nCoste acumulado: ${st.session_state["cost"]}\n\n"""
    #st.session_state["raw_text"] = raw_text  
    with open(LOG_PATH, "a", encoding="utf-8") as file:
        file.write(raw_text)

def actualizar_contador()->None:
    """Actualiza el contador de descargas del CV sumando 1 y añadiendo la fecha de la última descarga.
    """
    db_conn["ContadorCV"].update_many(
    {"_id" : CONTADOR_ID}, 
    {"$inc" : {"contador" : 1}, #incrementamos en 1
    "$set":{"fecha_ultimo" : format_datetime}},
    )

def insertar_db_preguntas_respuestas(db_schema:models.PreguntasRespuestas)->None:
    """Inserta en base de datos la pregunta y la respuesta asi como la fecha y hora.
    En formato de clase PreguntasRespuestas

    Parameters
    ----------
    db_schema : models.PreguntasRespuestas
        _description_
    """
    db_conn["PreguntasRespuestas"].insert_one(db_schema.dict(by_alias=True))  

def generar_id_sesion()->str:
    return "".join(random.choices(string.ascii_uppercase,k=4))

def actualizar_id_sesion()->dict:
    """Crea un diccionario con el id de sesión y el número de la pregunta (id).
    La idea es trackear las preguntas por id de sesión

    Returns
    -------
    dict
        Devuelve diccionario con el id de la sesión y el número de la pregunta
    """
    if "id_sesion" not in st.session_state:
        id_sesion = generar_id_sesion() 
        st.session_state["id_sesion"] = id_sesion
    else:
        id_sesion = st.session_state["id_sesion"]

    query_num = st.session_state.get("query_num",0) + 1
    st.session_state["query_num"] = query_num
    return {
        "id_sesion" : id_sesion,
        "query_num" :query_num,
    }

##############################

#inicializamos el dict de sesión en caso de no existir. mostramos historial
init_variables_sesion()

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
            help="Descarg el CV de STM en formato pdf"
        )

#importamos el script de la lógica de la IA
import LLMMemory as llmm

#Inicializamos mensaje de bienvenida
llmm.init_memory()

pregunta = st.chat_input(
    placeholder="Escribe aquí lo que quieras",
    )

if pregunta:
    #Obtenemos la respuesta de la IA
    response = llmm.get_response_with_memory(pregunta)
    try:     
        #mandar_email(pregunta,response,subject = "Preguntas sobre el CV")
        #log_to_file(pregunta,response)
        db_schema = models.PreguntasRespuestas(
            pregunta=pregunta,
            **st.session_state["detalle_usuario"].dict(),
            **response,
            **actualizar_id_sesion())
        insertar_db_preguntas_respuestas(db_schema)

    except pymongo.errors.ConnectionFailure:
        st.error("Error de conexión a la base de datos.")
    except pymongo.errors.OperationFailure:
        st.error("Error en la operación de la base de datos.")
    except pymongo.errors.ConfigurationError:
        st.error("Error de configuración de la base de datos.")
    except TypeError:
        st.error("Error de tipo de datos al intentar insertar en la base de datos.")
    except ValueError:
        st.error("Error de valor al intentar insertar en la base de datos.")
    except Exception as exc:
        st.error(f"Error inesperado: {exc}")        

## DEBUG ##
#st.session_state["detalle_usuario"]
#st.session_state
