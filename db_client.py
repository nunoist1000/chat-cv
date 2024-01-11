from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

db_client = MongoClient(os.environ["DB_MONGO"])
database = db_client["CHAT-CV"]

def get_database()-> MongoClient:
    return database

