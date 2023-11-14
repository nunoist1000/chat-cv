from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

db_client = MongoClient(os.environ["DB_MONGO"])

database = db_client["CHAT-CV"]

def get_database()-> MongoClient:
    return database

