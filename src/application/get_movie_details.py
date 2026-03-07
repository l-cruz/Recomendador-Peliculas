from src.infrastructure.tmdb_client import TMDBClient

class GetMovieDetails:
    def __init__(self):
        self.client = TMDBClient()

    def execute(self, movie_id: int, language: str = "es-ES") -> dict:
        endpoint = f"/movie/{movie_id}"
        params = {
            "language": language,
            "append_to_response": "videos,images"
        }
        return self.client.execute(endpoint, params)