from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from src.infrastructure.db_connection import get_db


class UserRepository:
    def __init__(self):
        db = get_db()
        self.collection = db["usuarios"]
        self._ensure_indexes()

    # ──────────────────────────────────────────
    # Índices
    # ──────────────────────────────────────────

    def _ensure_indexes(self) -> None:
        self.collection.create_index(
            [("favorites.tmdb_id", ASCENDING)],
            name="idx_favorites_tmdb_id"
        )
        # No se indexa my_catalog porque no se consulta usuarios por ese campo.
        # El flujo correcto es: extraer IDs del usuario → buscar películas por tmdb_id.

    # ──────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────

    def _to_object_id(self, user_id: str) -> ObjectId:
        return ObjectId(user_id)

    # ──────────────────────────────────────────
    # Usuarios
    # ──────────────────────────────────────────

    def create_user(self, name: str) -> str:
        user_data = {
            "name": name,
            "favorites": [],
            "my_catalog": [],
            "created_at": datetime.now(timezone.utc)
        }
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def list_users(self) -> list:
        return list(self.collection.find({}, {"name": 1, "_id": 1}))

    # ──────────────────────────────────────────
    # Catálogo personal
    # ──────────────────────────────────────────

    def add_to_my_catalog(self, user_id: str, tmdb_id: int) -> None:
        self.collection.update_one(
            {"_id": self._to_object_id(user_id)},
            {"$addToSet": {"my_catalog": tmdb_id}}
        )

    def get_my_catalog_ids(self, user_id: str) -> list:
        user = self.collection.find_one(
            {"_id": self._to_object_id(user_id)},
            {"my_catalog": 1}
        )
        return user.get("my_catalog", []) if user else []

    # ──────────────────────────────────────────
    # Favoritos
    # ──────────────────────────────────────────

    def add_favorite(self, user_id: str, tmdb_id: int, title: str,
                     personal_rating: int = None) -> bool:
        fav = {
            "tmdb_id": tmdb_id,
            "title": title,
            "added_at": datetime.now(timezone.utc)
        }
        if personal_rating is not None:
            fav["personal_rating"] = personal_rating

        result = self.collection.update_one(
            {
                "_id": self._to_object_id(user_id),
                "favorites.tmdb_id": {"$ne": tmdb_id}   # solo si no está ya
            },
            {"$push": {"favorites": fav}}
        )
        return result.modified_count > 0

    def get_favorites(self, user_id: str) -> list:

        user = self.collection.find_one(
            {"_id": self._to_object_id(user_id)},
            {"favorites": 1}
        )
        return user.get("favorites", []) if user else []

    def remove_favorite(self, user_id: str, tmdb_id: int) -> bool:
        result = self.collection.update_one(
            {"_id": self._to_object_id(user_id)},
            {"$pull": {"favorites": {"tmdb_id": tmdb_id}}}
        )
        return result.modified_count > 0

    def get_favorites_with_details(self, user_id: str) -> list:
        pipeline = [
            {"$match": {"_id": self._to_object_id(user_id)}},
            {"$unwind": "$favorites"},
            {
                "$lookup": {
                    "from": "peliculas",
                    "localField": "favorites.tmdb_id",
                    "foreignField": "tmdb_id",
                    "as": "movie_data"
                }
            },
            {"$unwind": {"path": "$movie_data", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "tmdb_id": "$favorites.tmdb_id",
                    "title": "$favorites.title",
                    "personal_rating": "$favorites.personal_rating",
                    "added_at": "$favorites.added_at",
                    "vote_average": "$movie_data.vote_average",
                    "genres": "$movie_data.genres",
                    "overview": "$movie_data.overview",
                    "release_year": "$movie_data.release_year",
                    "release_date": "$movie_data.release_date",
                    "poster_path": "$movie_data.poster_path"
                }
            },
            {"$sort": {"personal_rating": DESCENDING, "added_at": DESCENDING}}
        ]
        return list(self.collection.aggregate(pipeline))
