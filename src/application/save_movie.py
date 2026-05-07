from datetime import datetime, timezone

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
            "tmdb_id":          movie_data.get("id"),
            "title":            movie_data.get("title") or movie_data.get("original_title"),
            "original_title":   movie_data.get("original_title"),
            "overview":         movie_data.get("overview"),
            "vote_average":     movie_data.get("vote_average"),
            "vote_count":       movie_data.get("vote_count"),
            "genres":           [g["name"] for g in movie_data.get("genres", [])],
            "release_date":     release_date,
            "release_year":     release_year,
            "runtime":          movie_data.get("runtime"),
            "popularity":       movie_data.get("popularity"),
            "original_language": movie_data.get("original_language"),
            "adult":            movie_data.get("adult", False),
            "poster_path":      movie_data.get("poster_path"),
            "backdrop_path":    movie_data.get("backdrop_path"),
            "production_countries": [
                c["iso_3166_1"] for c in movie_data.get("production_countries", [])
            ],
            "spoken_languages": [
                l["iso_639_1"] for l in movie_data.get("spoken_languages", [])
            ],
            "updated_at":       datetime.now(timezone.utc),
        }

        self.db_client.execute(movie_to_save)
        return f"Película '{movie_to_save['title']}' guardada/actualizada con éxito en el catálogo local."
