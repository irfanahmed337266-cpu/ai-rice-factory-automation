from ml.predict import predict_production


def predict_factory_production(
    material: str,
    input_quantity: float,
    production_hour: int,
    production_weekday: int,
    previous_yield_rate: float,
    previous_waste_rate: float,
):
    result = predict_production(
        material=material,
        input_quantity=input_quantity,
        production_hour=production_hour,
        production_weekday=production_weekday,
        previous_yield_rate=previous_yield_rate,
        previous_waste_rate=previous_waste_rate,
    )

    return result