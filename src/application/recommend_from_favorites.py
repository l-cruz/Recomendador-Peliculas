from bson import ObjectId

from src.infrastructure.mongo_client import MongoDBClient
from src.infrastructure.user_repository import UserRepository


class RecommendFromFavorites:
    def __init__(self):
        self.user_repo = UserRepository()
        self.db_client = MongoDBClient()

    def execute(self, user_id: str, limit: int = 10) -> dict:
        genres_pipeline = [
            {"$match": {"_id": ObjectId(user_id)}},
            {"$unwind": "$favorites"},
            {
                "$lookup": {
                    "from": "peliculas",
                    "localField": "favorites.tmdb_id",
                    "foreignField": "tmdb_id",
                    "as": "movie_detail"
                }
            },
            {"$unwind": "$movie_detail"},
            {"$unwind": "$movie_detail.genres"},
            {
                "$group": {
                    "_id": "$movie_detail.genres",
                    "frequency": {"$sum": 1},
                    "personal_rating_sum": {
                        "$sum": {"$ifNull": ["$favorites.personal_rating", 0]}
                    }
                }
            },
            {"$sort": {"frequency": -1, "personal_rating_sum": -1}},
            {"$limit": 3}
        ]

        raw_profile = list(self.user_repo.collection.aggregate(genres_pipeline))
        if not raw_profile:
            return {"perfil_generos": [], "recomendaciones": []}

        top_genres = [genre_doc["_id"] for genre_doc in raw_profile]
        profile = [
            {"genero": genre_doc["_id"], "frecuencia": genre_doc["frequency"]}
            for genre_doc in raw_profile
        ]

        favorites = self.user_repo.get_favorites(user_id)
        favorite_ids = [favorite["tmdb_id"] for favorite in favorites if "tmdb_id" in favorite]

        recommendations_pipeline = [
            {
                "$match": {
                    "genres": {"$in": top_genres},
                    "tmdb_id": {"$nin": favorite_ids}
                }
            },
            {
                "$addFields": {
                    "generos_coincidentes": {
                        "$size": {
                            "$setIntersection": ["$genres", top_genres]
                        }
                    }
                }
            },
            {"$sort": {"generos_coincidentes": -1, "vote_average": -1}},
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "tmdb_id": 1,
                    "title": 1,
                    "genres": 1,
                    "vote_average": 1,
                    "release_date": 1,
                    "release_year": 1,
                    "overview": 1,
                    "generos_coincidentes": 1
                }
            }
        ]

        recommendations = list(self.db_client.collection.aggregate(recommendations_pipeline))

        return {
            "perfil_generos": profile,
            "recomendaciones": recommendations
        }