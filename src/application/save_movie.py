from src.infrastructure.mongo_client import MongoDBClient


class SaveMovie:
    def __init__(self):
        self.db_client = MongoDBClient()

    def execute(self, movie_data: dict) -> str:
        movie_to_save = {
            "tmdb_id": movie_data.get("id"),
            "title": movie_data.get("title"),
            "original_title": movie_data.get("original_title"),
            "overview": movie_data.get("overview"),
            "vote_average": movie_data.get("vote_average"),
            "genres": [genre["name"] for genre in movie_data.get("genres", [])],
            "release_date": movie_data.get("release_date"),
            "runtime": movie_data.get("runtime"),
            "popularity": movie_data.get("popularity")
        }

        return self.db_client.execute(movie_to_save)