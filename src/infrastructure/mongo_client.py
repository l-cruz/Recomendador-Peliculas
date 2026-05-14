from pymongo import ASCENDING, DESCENDING, TEXT
from src.infrastructure.db_connection import get_db

class MongoDBClient:
    def __init__(self):
        db = get_db()
        self.collection = db["peliculas"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.collection.create_index(
            [("tmdb_id", ASCENDING)],
            name="idx_tmdb_id",
            unique=True
        )

        self.collection.create_index(
            [
                ("genres", ASCENDING),
                ("vote_count", ASCENDING),
                ("release_year", ASCENDING),
                ("vote_average", DESCENDING)
            ],
            name="idx_genres_year_score_2"
        )

        self.collection.create_index(
            [("title", TEXT), ("overview", TEXT)],
            name="idx_fulltext",
            default_language="spanish"
        )

        self.collection.create_index(
            [("popularity", DESCENDING)],
            name="idx_popularity"
        )

        self.collection.create_index(
            [("vote_average", DESCENDING), ("vote_count", DESCENDING)],
            name="idx_rating_count"
        )

    def execute(self, document: dict) -> str:
        self.collection.update_one(
            {"tmdb_id": document["tmdb_id"]},
            {"$set": document},
            upsert=True
        )
        return "Guardado/Actualizado correctamente"
