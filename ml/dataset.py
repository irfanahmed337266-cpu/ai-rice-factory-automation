import pandas as pd

from ml.data import load_production_data, build_features


TARGET = "yield_rate"

FEATURES = [
    "material",
    "input_quantity",
    "production_hour",
    "production_weekday",
    "previous_yield_rate",
    "previous_waste_rate",
]


def create_training_dataset():
    df = load_production_data()
    df = build_features(df)

    if df.empty:
        raise ValueError("No completed production records found.")

    # Keep only columns needed for ML
    dataset = df[FEATURES + [TARGET]].copy()

    # Remove rows where target is missing
    dataset = dataset.dropna(subset=[TARGET])

    return dataset


if __name__ == "__main__":
    dataset = create_training_dataset()

    print("\n=== ML TRAINING DATASET ===")
    print(dataset.to_string(index=False))

    print("\n=== FEATURES ===")
    print(FEATURES)

    print("\n=== TARGET ===")
    print(TARGET)

    print("\n=== DATASET SHAPE ===")
    print(dataset.shape)

    print("\n=== TARGET DISTRIBUTION ===")
    print(dataset[TARGET].describe())