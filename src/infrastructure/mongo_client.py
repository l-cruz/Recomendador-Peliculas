import os
from dotenv import load_dotenv
from pymongo import ASCENDING, DESCENDING, TEXT, MongoClient

load_dotenv()


class MongoDBClient:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("No se ha encontrado la variable de entorno MONGO_URI.")

        self.client = MongoClient(uri)
        self.db = self.client["recomendador_db"]
        self.collection = self.db["peliculas"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.collection.create_index(
            [("tmdb_id", ASCENDING)],
            name="idx_tmdb_id",
            unique=True
        )

        self.collection.create_index(
            [("genres", ASCENDING), ("release_year", ASCENDING), ("vote_average", DESCENDING)],
            name="idx_genres_year_score"
        )

        self.collection.create_index(
            [("title", TEXT), ("overview", TEXT)],
            name="idx_fulltext",
            default_language="spanish"
        )

    def execute(self, document: dict) -> str:
        self.collection.update_one(
            {"tmdb_id": document["tmdb_id"]},
            {"$set": document},
            upsert=True
        )
        return "Guardado/Actualizado correctamente"