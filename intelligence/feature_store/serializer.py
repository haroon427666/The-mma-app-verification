"""Feature Store Serializer — import/export for artifacts.

Saves/loads features, embeddings, and rankings to disk.
"""

import json
import os
from typing import Any

import numpy as np


def save_json(data: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def save_vectors(vectors: dict[str, np.ndarray], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, **vectors)


def load_vectors(path: str) -> dict[str, np.ndarray]:
    return dict(np.load(path))


def save_rankings(rankings: list[dict], path: str) -> None:
    save_json({"rankings": rankings, "generated_at": str(np.datetime64("now"))}, path)


def load_rankings(path: str) -> list[dict]:
    return load_json(path).get("rankings", [])


def save_dataset(features: np.ndarray, labels: np.ndarray, ids: list[str],
                 feature_names: list[str], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(
        path,
        features=features, labels=labels,
        feature_names=np.array(feature_names, dtype="S"),
        ids=np.array(ids, dtype="S"),
    )


def load_dataset(path: str) -> dict[str, Any]:
    data = np.load(path, allow_pickle=True)
    return {
        "features": data["features"],
        "labels": data["labels"],
        "feature_names": [str(n) for n in data["feature_names"]],
        "ids": [str(i) for i in data["ids"]],
    }
