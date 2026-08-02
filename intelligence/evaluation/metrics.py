"""Evaluation — measures prediction accuracy, ranking quality, similarity quality.

Without evaluation, you never know whether changes improve the system.
"""

import numpy as np
from typing import Optional


def prediction_accuracy(
    predictions: np.ndarray,
    labels: np.ndarray,
    threshold: float = 0.5,
) -> dict:
    """Evaluate binary win prediction accuracy.

    Returns: accuracy, precision, recall, F1, AUC (simple), log loss.
    """
    pred_binary = (predictions >= threshold).astype(np.float32)

    tp = float(np.sum((pred_binary == 1) & (labels == 1)))
    tn = float(np.sum((pred_binary == 0) & (labels == 0)))
    fp = float(np.sum((pred_binary == 1) & (labels == 0)))
    fn = float(np.sum((pred_binary == 0) & (labels == 1)))

    accuracy = (tp + tn) / max(len(labels), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-10)

    # Simple log loss
    eps = 1e-10
    log_loss = -np.mean(labels * np.log(predictions + eps) + (1 - labels) * np.log(1 - predictions + eps))

    return {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "log_loss": round(log_loss, 4),
        "samples": len(labels),
    }


def ranking_quality(
    predicted_ranks: list[int],
    actual_ranks: list[int],
) -> dict:
    """Evaluate ranking quality against ground truth (official UFC rankings).

    Returns: Kendall's tau, top-5 overlap, top-10 overlap.
    """
    n = len(predicted_ranks)
    if n < 2:
        return {"error": "need at least 2 ranked fighters"}

    # Kendall's tau
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            pred_order = predicted_ranks[i] < predicted_ranks[j]
            actual_order = actual_ranks[i] < actual_ranks[j]
            if pred_order == actual_order:
                concordant += 1
            else:
                discordant += 1

    total = concordant + discordant
    tau = (concordant - discordant) / max(total, 1)

    # Top-K overlap
    top5_pred = set(range(min(5, n)))
    top5_actual = set(np.argsort(actual_ranks)[:5].tolist())
    top5_overlap = len(top5_pred & top5_actual) / 5

    return {
        "kendall_tau": round(tau, 4),
        "top5_overlap": round(top5_overlap, 4),
        "total_fighters": n,
    }


def similarity_quality(
    neighbor_labels: list[list[str]],
    query_labels: list[str],
) -> dict:
    """Evaluate similarity search quality.

    For each query, check if its top-3 neighbors share the same style/category.
    """
    hits_at_1 = 0
    hits_at_3 = 0
    total = max(len(query_labels), 1)

    for i, q_label in enumerate(query_labels):
        neighbors = neighbor_labels[i][:3] if i < len(neighbor_labels) else []
        if neighbors and neighbors[0] == q_label:
            hits_at_1 += 1
        if any(n == q_label for n in neighbors):
            hits_at_3 += 1

    return {
        "hit_at_1": round(hits_at_1 / total, 4),
        "hit_at_3": round(hits_at_3 / total, 4),
        "queries": total,
    }


def clustering_quality(
    labels: np.ndarray,
    vectors: np.ndarray,
) -> dict:
    """Evaluate clustering quality (silhouette score)."""
    if len(set(labels)) < 2:
        return {"error": "need at least 2 clusters"}

    from sklearn.metrics import silhouette_score
    score = silhouette_score(vectors, labels)
    return {
        "silhouette_score": round(score, 4),
        "n_clusters": len(set(labels)),
        "n_samples": len(labels),
    }
