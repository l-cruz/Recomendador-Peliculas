from src.infrastructure.user_repository import UserRepository


class UpdateFavoriteRating:
    def __init__(self):
        self.user_repo = UserRepository()

    def execute(self, user_id: str, tmdb_id: int, new_rating: int) -> dict:
        if not (1 <= new_rating <= 10):
            return {
                "ok": False,
                "mensaje": "La puntuación debe estar entre 1 y 10."
            }

        updated = self.user_repo.update_favorite_rating(
            user_id=user_id,
            tmdb_id=tmdb_id,
            new_rating=new_rating
        )

        if updated:
            return {
                "ok": True,
                "mensaje": f"Puntuación actualizada a {new_rating}/10."
            }

        return {
            "ok": False,
            "mensaje": "Esa película no está en tus favoritas o la nota es la misma."
        }