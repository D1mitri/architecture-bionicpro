from sqlalchemy import create_engine, text
import pandas as pd
from typing import List, Optional

from .config import settings

engine = create_engine(settings.database_url)

def execute_query(query: str, params: dict = None) -> pd.DataFrame:
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection, params=params)

def get_user_report(user_id: int) -> Optional[dict]:
    query = """
    SELECT
        user_id,
        customer_name,
        customer_email,
        region,
        account_status,
        subscription_type,
        avg_sensor_data,
        avg_battery_level,
        total_readings,
        data_quality_score,
        battery_health,
        first_reading,
        last_reading,
        load_date,
        etl_timestamp
    FROM customer_telemetry_mart
    WHERE user_id = :user_id
    ORDER BY load_date DESC, etl_timestamp DESC
    LIMIT 1
    """

    df = execute_query(query, {"user_id": user_id})

    if df.empty:
        return None

    return df.iloc[0].to_dict()

def get_user_history(user_id: int, limit: int = 30) -> List[dict]:
    query = """
    SELECT
        load_date,
        avg_sensor_data,
        avg_battery_level,
        total_readings,
        data_quality_score,
        battery_health,
        etl_timestamp
    FROM customer_telemetry_mart
    WHERE user_id = :user_id
    ORDER BY load_date DESC
    LIMIT :limit
    """

    df = execute_query(query, {"user_id": user_id, "limit": limit})
    return df.to_dict(orient="records")