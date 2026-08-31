import joblib
import pandas as pd

from ml.train import MODEL_PATH


FEATURES = [
    "material",
    "input_quantity",
    "production_hour",
    "production_weekday",
    "previous_yield_rate",
    "previous_waste_rate",
]


def load_model():
    return joblib.load(MODEL_PATH)


def predict_production(
    material: str,
    input_quantity: float,
    production_hour: int,
    production_weekday: int,
    previous_yield_rate: float,
    previous_waste_rate: float,
):
    model = load_model()

    data = pd.DataFrame(
        [
            {
                "material": material,
                "input_quantity": input_quantity,
                "production_hour": production_hour,
                "production_weekday": production_weekday,
                "previous_yield_rate": previous_yield_rate,
                "previous_waste_rate": previous_waste_rate,
            }
        ]
    )

    predicted_yield = float(model.predict(data)[0])

    predicted_output = input_quantity * predicted_yield
    predicted_waste = input_quantity - predicted_output

    return {
        "material": material,
        "input_quantity": input_quantity,
        "predicted_yield_rate": round(predicted_yield, 4),
        "predicted_output_quantity": round(predicted_output, 2),
        "predicted_waste_quantity": round(predicted_waste, 2),
    }


if __name__ == "__main__":

    result = predict_production(
        material="Phak",
        input_quantity=500,
        production_hour=10,
        production_weekday=0,
        previous_yield_rate=0.90,
        previous_waste_rate=0.10,
    )

    print("\n=== ML PREDICTION ===")

    for key, value in result.items():
        print(f"{key}: {value}")