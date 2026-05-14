from bson import ObjectId

from src.infrastructure.db_connection import get_db


class GetUserStats:
    """
    Genera estadísticas personalizadas del usuario a partir de sus favoritas,
    cruzando la colección usuarios con peliculas mediante $lookup.
    """

    def __init__(self):
        self.db = get_db()

    def execute(self, user_id: str) -> dict:
        pipeline = [
            {"$match": {"_id": ObjectId(user_id)}},
            {"$unwind": {"path": "$favorites", "preserveNullAndEmptyArrays": False}},
            {
                "$lookup": {
                    "from": "peliculas",
                    "localField": "favorites.tmdb_id",
                    "foreignField": "tmdb_id",
                    "as": "movie_detail"
                }
            },
            {"$unwind": {"path": "$movie_detail", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": "$_id",
                    "user_name": {"$first": "$name"},
                    "catalog_size": {
                        "$first": {
                            "$size": {"$ifNull": ["$my_catalog", []]}
                        }
                    },
                    "favorites_data": {
                        "$push": {
                            "tmdb_id": "$favorites.tmdb_id",
                            "title": "$movie_detail.title",
                            "personal_rating": "$favorites.personal_rating",
                            "tmdb_rating": "$movie_detail.vote_average",
                            "genres": "$movie_detail.genres",
                            "release_year": "$movie_detail.release_year",
                            "added_at": "$favorites.added_at"
                        }
                    }
                }
            },
            {
                "$facet": {
                    "resumen": [
                        {
                            "$project": {
                                "user_name": 1,
                                "catalog_size": 1,
                                "total_favoritas": {"$size": "$favorites_data"},
                                "nota_media_personal": {
                                    "$avg": {
                                        "$map": {
                                            "input": {
                                                "$filter": {
                                                    "input": "$favorites_data",
                                                    "as": "f",
                                                    "cond": {
                                                        "$gt": [
                                                            {
                                                                "$ifNull": [
                                                                    "$$f.personal_rating",
                                                                    0
                                                                ]
                                                            },
                                                            0
                                                        ]
                                                    }
                                                }
                                            },
                                            "as": "f",
                                            "in": "$$f.personal_rating"
                                        }
                                    }
                                },
                                "nota_media_tmdb": {
                                    "$avg": {
                                        "$map": {
                                            "input": "$favorites_data",
                                            "as": "f",
                                            "in": "$$f.tmdb_rating"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "top_generos": [
                        {"$unwind": "$favorites_data"},
                        {"$unwind": "$favorites_data.genres"},
                        {
                            "$group": {
                                "_id": "$favorites_data.genres",
                                "count": {"$sum": 1},
                                "avg_personal_rating": {
                                    "$avg": "$favorites_data.personal_rating"
                                }
                            }
                        },
                        {"$sort": {"count": -1}},
                        {"$limit": 5}
                    ],
                    "por_decada": [
                        {"$unwind": "$favorites_data"},
                        {
                            "$match": {
                                "favorites_data.release_year": {"$ne": None}
                            }
                        },
                        {
                            "$group": {
                                "_id": {
                                    "$subtract": [
                                        "$favorites_data.release_year",
                                        {
                                            "$mod": [
                                                "$favorites_data.release_year",
                                                10
                                            ]
                                        }
                                    ]
                                },
                                "total": {"$sum": 1}
                            }
                        },
                        {"$sort": {"total": -1}},
                        {"$limit": 5}
                    ],
                    "mejor_puntuada": [
                        {"$unwind": "$favorites_data"},
                        {
                            "$match": {
                                "favorites_data.personal_rating": {"$gt": 0}
                            }
                        },
                        {"$sort": {"favorites_data.personal_rating": -1}},
                        {"$limit": 1},
                        {
                            "$project": {
                                "_id": 0,
                                "title": "$favorites_data.title",
                                "personal_rating": "$favorites_data.personal_rating",
                                "tmdb_rating": "$favorites_data.tmdb_rating"
                            }
                        }
                    ],
                    "peor_puntuada": [
                        {"$unwind": "$favorites_data"},
                        {
                            "$match": {
                                "favorites_data.personal_rating": {"$gt": 0}
                            }
                        },
                        {"$sort": {"favorites_data.personal_rating": 1}},
                        {"$limit": 1},
                        {
                            "$project": {
                                "_id": 0,
                                "title": "$favorites_data.title",
                                "personal_rating": "$favorites_data.personal_rating",
                                "tmdb_rating": "$favorites_data.tmdb_rating"
                            }
                        }
                    ]
                }
            }
        ]

        result = list(self.db["usuarios"].aggregate(pipeline))
        return result[0] if result else {}