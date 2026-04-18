from src.infrastructure.mongo_client import MongoDBClient
from src.infrastructure.user_repository import UserRepository


class AddFavorite:
    def __init__(self):
        self.user_repo = UserRepository()
        self.db_client = MongoDBClient()

    def execute(self, user_id: str, tmdb_id: int, personal_rating: int = None) -> dict:
        if personal_rating is not None and not (1 <= personal_rating <= 10):
            return {
                "ok": False,
                "mensaje": "La puntuación personal debe estar entre 1 y 10."
            }

        movie = self.db_client.collection.find_one(
            {"tmdb_id": tmdb_id},
            {"title": 1, "_id": 0}
        )

        if not movie:
            return {
                "ok": False,
                "mensaje": (
                    f"La película con tmdb_id={tmdb_id} no está en tu catálogo local. "
                    f"Guárdala primero desde TMDB."
                )
            }

        title = movie["title"]
        added = self.user_repo.add_favorite(
            user_id=user_id,
            tmdb_id=tmdb_id,
            title=title,
            personal_rating=personal_rating
        )

        if added:
            return {"ok": True, "mensaje": f"'{title}' añadida a tus favoritas."}

        return {"ok": False, "mensaje": f"'{title}' ya estaba en tus favoritas."}