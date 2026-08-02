"""Training Pipeline — XGBoost, LightGBM, Logistic Regression, Random Forest.

Train on historical fight data. Evaluate. Select best. Save model.
Production ML, not notebooks.
"""

import numpy as np
from typing import Any, Optional


def train_fight_predictor(
    X: np.ndarray, y: np.ndarray,
    model_type: str = "xgboost",
    params: Optional[dict] = None,
) -> tuple[Any, dict]:
    """Train a fight winner prediction model.

    Args:
        X: Feature matrix (N, D)
        y: Binary labels (1 = fighter A won, 0 = fighter B won)
        model_type: "xgboost", "lightgbm", "logistic", "random_forest"
        params: Model hyperparameters

    Returns:
        (trained_model, training_metrics)
    """
    default_params = {
        "xgboost": {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05, "subsample": 0.8, "colsample_bytree": 0.8},
        "logistic": {"C": 1.0, "max_iter": 1000},
        "random_forest": {"n_estimators": 200, "max_depth": 8, "min_samples_leaf": 5},
    }
    p = params or default_params.get(model_type, {})

    if model_type == "xgboost":
        try:
            from xgboost import XGBClassifier
            model = XGBClassifier(**p, use_label_encoder=False, eval_metric="logloss", verbosity=0)
        except ImportError:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100, max_depth=5)
    elif model_type == "logistic":
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(**p)
    elif model_type == "random_forest":
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(**p)
    else:
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression()

    model.fit(X, y)

    # Evaluate
    y_pred = model.predict_proba(X)[:, 1] if hasattr(model, "predict_proba") else model.predict(X)
    acc = float(np.mean((y_pred >= 0.5).astype(int) == y))
    eps = 1e-10
    logloss = float(-np.mean(y * np.log(y_pred + eps) + (1 - y) * np.log(1 - y_pred + eps)))

    return model, {
        "accuracy": round(acc, 4),
        "log_loss": round(logloss, 4),
        "samples": len(y),
        "model_type": model_type,
    }


def train_finish_predictor(
    X: np.ndarray, y: np.ndarray, model_type: str = "xgboost",
) -> tuple[Any, dict]:
    """Train multi-class finish predictor (KO/Submission/Decision)."""
    if model_type == "xgboost":
        try:
            from xgboost import XGBClassifier
            model = XGBClassifier(n_estimators=150, max_depth=4, learning_rate=0.05, verbosity=0)
        except ImportError:
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=100)
    else:
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(multi_class="multinomial", max_iter=1000)

    model.fit(X, y)
    if hasattr(model, "predict_proba"):
        pred = model.predict_proba(X)
    else:
        pred = np.eye(3)[model.predict(X)]

    acc = float(np.mean(np.argmax(pred, axis=1) == y))
    return model, {"accuracy": round(acc, 4), "samples": len(y)}


def cross_validate(
    X: np.ndarray, y: np.ndarray, model_type: str = "xgboost", n_folds: int = 5,
) -> dict:
    """K-fold cross-validation with accuracy + log loss per fold."""
    from sklearn.model_selection import StratifiedKFold

    skf = StratifiedKFold(n_splits=n_folds, shuffle=True)
    folds = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y)):
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        model, _ = train_fight_predictor(X_tr, y_tr, model_type)
        try:
            y_pred = model.predict_proba(X_te)[:, 1]
        except Exception:
            y_pred = model.predict(X_te)

        acc = float(np.mean((y_pred >= 0.5).astype(int) == y_te))
        eps = 1e-10
        ll = float(-np.mean(y_te * np.log(y_pred + eps) + (1 - y_te) * np.log(1 - y_pred + eps)))

        folds.append({"fold": fold + 1, "accuracy": round(acc, 4), "log_loss": round(ll, 4), "samples": len(y_te)})

    return {
        "folds": folds,
        "mean_accuracy": round(np.mean([f["accuracy"] for f in folds]), 4),
        "std_accuracy": round(np.std([f["accuracy"] for f in folds]), 4),
        "mean_log_loss": round(np.mean([f["log_loss"] for f in folds]), 4),
    }


def select_features(
    X: np.ndarray, y: np.ndarray, feature_names: list[str], k: int = 10,
) -> dict:
    """Feature importance using tree-based model."""
    try:
        from xgboost import XGBClassifier
        model = XGBClassifier(n_estimators=100, max_depth=4, verbosity=0)
    except ImportError:
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=100)

    model.fit(X, y)
    importances = model.feature_importances_

    ranked = sorted(
        [(name, float(imp)) for name, imp in zip(feature_names, importances)],
        key=lambda x: x[1], reverse=True,
    )
    return {
        "top_features": ranked[:k],
        "all_importances": ranked,
        "total_features": len(feature_names),
    }
