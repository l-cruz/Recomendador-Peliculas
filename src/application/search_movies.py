from src.infrastructure.tmdb_client import TMDBClient

class SearchMovies:
    def __init__(self):
        self.client = TMDBClient()

    def execute(self, query: str, language: str = "es-ES") -> dict:
        endpoint = "/search/movie"
        params = {
            "query": query,
            "language": language
        }
        return self.client.execute(endpoint, params)