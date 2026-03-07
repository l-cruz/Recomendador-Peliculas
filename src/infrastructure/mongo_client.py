import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

class MongoDBClient:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client["recomendador_db"]
        self.collection = self.db["peliculas"]

    def execute(self, document: dict) -> str:
        result = self.collection.update_one(
            {"tmdb_id": document["tmdb_id"]},
            {"$set": document},
            upsert=True
        )
        return "Guardado/Actualizado correctamente"