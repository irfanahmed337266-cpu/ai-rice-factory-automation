import pandas as pd

from sklearn.metrics import mean_absolute_error, mean_squared_error

from ml.dataset import create_training_dataset, FEATURES, TARGET
from ml.train import build_model


MIN_TRAINING_ROWS = 20


def evaluate_model():

    dataset = create_training_dataset()

    print("\n=== MODEL EVALUATION ===")

    print(f"Dataset rows: {len(dataset)}")

    # Safety check
    if len(dataset) < MIN_TRAINING_ROWS:
        print(
            f"\nWARNING: Only {len(dataset)} production records available."
        )
        print(
            f"At least {MIN_TRAINING_ROWS} records are recommended "
            "before trusting ML performance metrics."
        )

        print("\nCurrent model should be treated as experimental.")

    X = dataset[FEATURES]
    y = dataset[TARGET]

    model = build_model()

    # For the current tiny dataset we fit on available data
    # only to inspect model behavior.
    model.fit(X, y)

    predictions = model.predict(X)

    mae = mean_absolute_error(y, predictions)

    rmse = mean_squared_error(
        y,
        predictions,
    ) ** 0.5

    print(f"\nMAE: {mae:.6f}")
    print(f"RMSE: {rmse:.6f}")

    print("\n=== ACTUAL VS PREDICTED ===")

    results = pd.DataFrame(
        {
            "actual_yield": y.values,
            "predicted_yield": predictions,
            "error": y.values - predictions,
        }
    )

    print(results.to_string(index=False))


if __name__ == "__main__":
    evaluate_model()