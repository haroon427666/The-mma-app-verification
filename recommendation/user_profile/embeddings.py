"""Profile embeddings — creates vector embeddings from user profiles.

Enables: user-user similarity, cold-start handling, cluster membership.
"""

import numpy as np
from recommendation.user_profile.builder import UserProfile


def embed_profile(profile: UserProfile) -> np.ndarray:
    return profile.to_vector()


def profile_similarity(p1: UserProfile, p2: UserProfile) -> float:
    a, b = p1.to_vector(), p2.to_vector()
    return float(np.dot(a, b))


def find_similar_users(
    user_id: str,
    profiles: dict[str, UserProfile],
    k: int = 10,
) -> list[tuple[str, float]]:
    if user_id not in profiles:
        return []
    query = profiles[user_id].to_vector()
    results = []
    for uid, profile in profiles.items():
        if uid != user_id:
            sim = float(np.dot(query, profile.to_vector()))
            results.append((uid, sim))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:k]
