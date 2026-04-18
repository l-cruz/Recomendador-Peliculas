import os
from datetime import datetime, timezone
from typing import List, Optional
import certifi
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

load_dotenv()


class UserRepository:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise ValueError("No se ha encontrado la variable de entorno MONGO_URI.")

        client = MongoClient(uri, tlsCAFile=certifi.where())
        db = client["recomendador_db"]
        self.collection = db["usuarios"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.collection.create_index(
            [("name", ASCENDING)],
            name="idx_user_name"
        )
        self.collection.create_index(
            [("favorites.tmdb_id", ASCENDING)],
            name="idx_favorites_tmdb_id"
        )

    def _to_object_id(self, user_id: str) -> ObjectId:
        try:
            return ObjectId(user_id)
        except Exception as exc:
            raise ValueError("El user_id no tiene un formato válido de ObjectId.") from exc

    def create_user(self, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("El nombre del usuario no puede estar vacío.")

        existing_user = self.get_user_by_name(name)
        if existing_user:
            return str(existing_user["_id"])

        result = self.collection.insert_one({
            "name": name,
            "favorites": [],
            "recommendation_history": []
        })
        return str(result.inserted_id)

    def get_user(self, user_id: str) -> Optional[dict]:
        return self.collection.find_one({"_id": self._to_object_id(user_id)})

    def get_user_by_name(self, name: str) -> Optional[dict]:
        return self.collection.find_one({"name": name})

    def list_users(self) -> List[dict]:
        return list(self.collection.find({}, {"name": 1}))

    def add_favorite(
        self,
        user_id: str,
        tmdb_id: int,
        title: str,
        personal_rating: Optional[int] = None
    ) -> bool:
        if personal_rating is not None and not (1 <= personal_rating <= 10):
            raise ValueError("La puntuación personal debe estar entre 1 y 10.")

        already_exists = self.collection.count_documents({
            "_id": self._to_object_id(user_id),
            "favorites.tmdb_id": tmdb_id
        })
        if already_exists > 0:
            return False

        favorite = {
            "tmdb_id": tmdb_id,
            "title": title,
            "added_at": datetime.now(timezone.utc),
            "personal_rating": personal_rating
        }

        result = self.collection.update_one(
            {"_id": self._to_object_id(user_id)},
            {"$push": {"favorites": favorite}}
        )
        return result.modified_count > 0

    def remove_favorite(self, user_id: str, tmdb_id: int) -> bool:
        result = self.collection.update_one(
            {"_id": self._to_object_id(user_id)},
            {"$pull": {"favorites": {"tmdb_id": tmdb_id}}}
        )
        return result.modified_count > 0

    def update_favorite_score(self, user_id: str, tmdb_id: int, new_rating: int) -> bool:
        if not (1 <= new_rating <= 10):
            raise ValueError("La puntuación personal debe estar entre 1 y 10.")

        result = self.collection.update_one(
            {
                "_id": self._to_object_id(user_id),
                "favorites.tmdb_id": tmdb_id
            },
            {
                "$set": {
                    "favorites.$.personal_rating": new_rating
                }
            }
        )
        return result.modified_count > 0

    def get_favorites(self, user_id: str) -> list:
        user = self.collection.find_one(
            {"_id": self._to_object_id(user_id)},
            {"favorites": 1, "_id": 0}
        )
        return user.get("favorites", []) if user else []

    def save_recommendation_history(self, user_id: str, genres: list, tmdb_ids: list) -> None:
        self.collection.update_one(
            {"_id": self._to_object_id(user_id)},
            {
                "$push": {
                    "recommendation_history": {
                        "created_at": datetime.now(timezone.utc),
                        "genres_detected": genres,
                        "recommended_tmdb_ids": tmdb_ids
                    }
                }
            }
        )