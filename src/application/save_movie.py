from src.infrastructure.mongo_client import MongoDBClient


class SaveMovie:
    def __init__(self):
        self.db_client = MongoDBClient()

    def execute(self, movie_data: dict) -> str:
        release_date = movie_data.get("release_date")
        release_year = None

        if isinstance(release_date, str) and len(release_date) >= 4 and release_date[:4].isdigit():
            release_year = int(release_date[:4])

        movie_to_save = {
            "tmdb_id": movie_data.get("id"),
            "title": movie_data.get("title") or movie_data.get("original_title"),
            "original_title": movie_data.get("original_title"),
            "overview": movie_data.get("overview"),
            "vote_average": movie_data.get("vote_average"),
            "genres": [genre["name"] for genre in movie_data.get("genres", [])],
            "release_date": release_date,
            "release_year": release_year,
            "runtime": movie_data.get("runtime"),
            "popularity": movie_data.get("popularity"),
            "original_language": movie_data.get("original_language"),
            "adult": movie_data.get("adult", False),
            "poster_path": movie_data.get("poster_path")
        }

        return self.db_client.execute(movie_to_save)