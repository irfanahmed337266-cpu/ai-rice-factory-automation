import os
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ml.dataset import create_training_dataset, FEATURES, TARGET


MODEL_DIR = "ml/models"
MODEL_PATH = os.path.join(MODEL_DIR, "yield_model.joblib")


CATEGORICAL_FEATURES = [
    "material",
]

NUMERIC_FEATURES = [
    "input_quantity",
    "production_hour",
    "production_weekday",
    "previous_yield_rate",
    "previous_waste_rate",
]


def build_model():

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                "passthrough",
                NUMERIC_FEATURES,
            ),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=100,
        random_state=42,
        min_samples_leaf=1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    return pipeline


def train():

    dataset = create_training_dataset()

    X = dataset[FEATURES]
    y = dataset[TARGET]

    print("\n=== TRAINING DATA ===")
    print(X)

    print("\n=== TARGET ===")
    print(y)

    model = build_model()

    model.fit(X, y)

    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(model, MODEL_PATH)

    print("\n=== TRAINING COMPLETE ===")
    print(f"Rows used: {len(dataset)}")
    print(f"Features: {len(FEATURES)}")
    print(f"Model saved: {MODEL_PATH}")

    return model


if __name__ == "__main__":
    train()