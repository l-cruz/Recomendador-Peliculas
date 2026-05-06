import os
from datetime import datetime, timezone
import certifi
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

load_dotenv()

class UserRepository:
    def __init__(self):
        uri = os.getenv("MONGO_URI")
        client = MongoClient(uri, tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)
        db = client["recomendador_db"]
        self.collection = db["usuarios"]

    def _to_object_id(self, user_id: str) -> ObjectId:
        return ObjectId(user_id)

    def create_user(self, name: str) -> str:
        user_data = {
            "name": name,
            "favorites": [],
            "my_catalog": [], # IDs de pelis vinculadas a este usuario
            "created_at": datetime.now(timezone.utc)
        }
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def list_users(self) -> list:
        return list(self.collection.find({}, {"name": 1, "_id": 1}))

    def add_to_my_catalog(self, user_id: str, tmdb_id: int):
        self.collection.update_one(
            {"_id": self._to_object_id(user_id)},
            {"$addToSet": {"my_catalog": tmdb_id}}
        )

    def get_my_catalog_ids(self, user_id: str) -> list:
        user = self.collection.find_one({"_id": self._to_object_id(user_id)}, {"my_catalog": 1})
        return user.get("my_catalog", []) if user else []

    def add_favorite(self, user_id: str, tmdb_id: int, title: str, personal_rating: int = None):
        fav = {"tmdb_id": tmdb_id, "title": title, "added_at": datetime.now(timezone.utc)}
        if personal_rating: fav["personal_rating"] = personal_rating
        self.collection.update_one({"_id": self._to_object_id(user_id)}, {"$addToSet": {"favorites": fav}})