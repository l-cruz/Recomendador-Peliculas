from src.infrastructure.user_repository import UserRepository


class RemoveFavorite:
    def __init__(self):
        self.user_repo = UserRepository()

    def execute(self, user_id: str, tmdb_id: int) -> dict:
        removed = self.user_repo.remove_favorite(user_id=user_id, tmdb_id=tmdb_id)

        if removed:
            return {
                "ok": True,
                "mensaje": f"Película con tmdb_id={tmdb_id} eliminada de tus favoritas."
            }

        return {
            "ok": False,
            "mensaje": "Esa película no estaba en tus favoritas."
        }