from src.infrastructure.tmdb_client import TMDBClient

class DiscoverMovies:
    def __init__(self):
        self.client = TMDBClient()

    def execute(self, sort_by: str = "popularity.desc", language: str = "es-ES", page: int = 1) -> dict:
        endpoint = "/discover/movie"
        params = {
            "sort_by": sort_by,
            "language": language,
            "page": page
        }
        return self.client.execute(endpoint, params)