from sqlalchemy import text
import pandas as pd

from app.database import engine


def load_production_data() -> pd.DataFrame:
    query = """
    SELECT
        p.id AS production_id,
        m.name AS material,
        p.input_quantity,
        p.output_quantity,
        p.waste_quantity,
        p.status,
        p.created_at,
        p.output_product_id,

        ROUND(
            p.output_quantity::numeric
            / NULLIF(p.input_quantity, 0),
            4
        ) AS yield_rate,

        ROUND(
            p.waste_quantity::numeric
            / NULLIF(p.input_quantity, 0),
            4
        ) AS waste_rate

    FROM production p

    LEFT JOIN materials m
        ON m.id = p.input_material_id

    WHERE p.status = 'Completed'

    ORDER BY p.created_at
    """

    with engine.connect() as connection:
        df = pd.read_sql(text(query), connection)

    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if df.empty:
        return df

    # Time features
    df["production_hour"] = (
        pd.to_datetime(df["created_at"]).dt.hour
    )

    df["production_weekday"] = (
        pd.to_datetime(df["created_at"]).dt.dayofweek
    )

    # Previous yield for the same material
    df["previous_yield_rate"] = (
        df.groupby("material")["yield_rate"]
        .shift(1)
    )

    # Previous waste rate
    df["previous_waste_rate"] = (
        df.groupby("material")["waste_rate"]
        .shift(1)
    )

    # Fill first observation for each material
    df["previous_yield_rate"] = (
        df["previous_yield_rate"]
        .fillna(df["yield_rate"].mean())
    )

    df["previous_waste_rate"] = (
        df["previous_waste_rate"]
        .fillna(df["waste_rate"].mean())
    )

    return df


if __name__ == "__main__":
    df = load_production_data()

    print("\n=== RAW PRODUCTION DATA ===")
    print(df.to_string(index=False))

    df = build_features(df)

    print("\n=== ML FEATURE DATASET ===")
    print(df.to_string(index=False))

    print("\n=== DATASET SHAPE ===")
    print(df.shape)

    print("\n=== COLUMNS ===")
    print(list(df.columns))