from bson import ObjectId

from src.infrastructure.mongo_client import MongoDBClient
from src.infrastructure.user_repository import UserRepository


class RecommendFromFavorites:
    def __init__(self):
        self.user_repo = UserRepository()
        self.db_client = MongoDBClient()

    def execute(self, user_id: str, limit: int = 10) -> dict:
        # 1. Perfil de géneros: frecuencia + nota media personal por género
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
                    "rated_count": {
                        "$sum": {
                            "$cond": [
                                {"$gt": [{"$ifNull": ["$favorites.personal_rating", 0]}, 0]},
                                1,
                                0
                            ]
                        }
                    },
                    "personal_rating_sum": {
                        "$sum": {"$ifNull": ["$favorites.personal_rating", 0]}
                    }
                }
            },
            {
                "$addFields": {
                    "avg_personal_rating": {
                        "$cond": [
                            {"$gt": ["$rated_count", 0]},
                            {"$divide": ["$personal_rating_sum", "$rated_count"]},
                            0
                        ]
                    }
                }
            },
            {
                "$addFields": {
                    "genre_weight": {
                        "$add": [
                            "$frequency",
                            {"$divide": ["$avg_personal_rating", 10]}
                        ]
                    }
                }
            },
            {"$sort": {"genre_weight": -1}},
            {"$limit": 3}
        ]

        raw_profile = list(self.user_repo.collection.aggregate(genres_pipeline))

        if not raw_profile:
            return {
                "perfil_generos": [],
                "recomendaciones": []
            }

        top_genres = [genre_doc["_id"] for genre_doc in raw_profile]

        profile = [
            {
                "genero": genre_doc["_id"],
                "frecuencia": genre_doc["frequency"],
                "nota_media_personal": round(genre_doc.get("avg_personal_rating", 0), 1),
                "peso": round(genre_doc.get("genre_weight", 0), 2)
            }
            for genre_doc in raw_profile
        ]

        # 2. Sacamos los IDs de las favoritas para no recomendarlas de nuevo
        favorites = self.user_repo.get_favorites(user_id)
        favorite_ids = [
            favorite["tmdb_id"]
            for favorite in favorites
            if "tmdb_id" in favorite
        ]

        # 3. Preparamos las ramas del $switch para ponderar cada género
        genre_weight_branches = [
            {
                "case": {"$eq": ["$$this", genre_doc["_id"]]},
                "then": genre_doc["genre_weight"]
            }
            for genre_doc in raw_profile
        ]

        # 4. Pipeline de recomendaciones con score ponderado
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
            {
                "$addFields": {
                    "recommendation_score": {
                        "$add": [
                            {
                                "$reduce": {
                                    "input": {
                                        "$filter": {
                                            "input": "$genres",
                                            "as": "g",
                                            "cond": {"$in": ["$$g", top_genres]}
                                        }
                                    },
                                    "initialValue": 0,
                                    "in": {
                                        "$add": [
                                            "$$value",
                                            {
                                                "$switch": {
                                                    "branches": genre_weight_branches,
                                                    "default": 0
                                                }
                                            }
                                        ]
                                    }
                                }
                            },
                            {
                                "$divide": [
                                    {"$ifNull": ["$vote_average", 0]},
                                    10
                                ]
                            }
                        ]
                    }
                }
            },
            {
                "$sort": {
                    "recommendation_score": -1,
                    "generos_coincidentes": -1,
                    "vote_average": -1
                }
            },
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
                    "generos_coincidentes": 1,
                    "recommendation_score": {
                        "$round": ["$recommendation_score", 2]
                    }
                }
            }
        ]

        recommendations = list(
            self.db_client.collection.aggregate(recommendations_pipeline)
        )

        return {
            "perfil_generos": profile,
            "recomendaciones": recommendations
        }