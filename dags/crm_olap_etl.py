from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import create_engine

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 12, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def extract_crm_data():
    crm_hook = PostgresHook(postgres_conn_id='crm_connection')

    query = """
    SELECT 
        user_id,
        customer_name,
        customer_email,
        registration_date,
        subscription_type,
        region,
        account_status
    FROM customers
    WHERE updated_at >= NOW() - INTERVAL '24 HOURS'
        OR created_at >= NOW() - INTERVAL '24 HOURS'
    """
    
    df_crm = crm_hook.get_pandas_df(query)

    df_crm.to_csv('/tmp/crm_data_extract.csv', index=False)
    
    return f"Extracted {len(df_crm)} records from CRM"

def extract_telemetry_data():
    telemetry_hook = PostgresHook(postgres_conn_id='write_to_postgres')

    check_query = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'bionicpro_table'
      AND column_name = 'created_at';
    """

    has_created_at = telemetry_hook.get_first(check_query)

    if has_created_at:
        query = """
        SELECT
            user_id,
            AVG(mio_sensor_data) as avg_sensor_data,
            AVG(battery_level) as avg_battery_level,
            COUNT(*) as total_readings,
            MIN(created_at) as first_reading,
            MAX(created_at) as last_reading
        FROM bionicpro_table
        WHERE created_at >= NOW() - INTERVAL '24 HOURS'
        GROUP BY user_id
        """
    else:
        import logging
        logging.warning("Column 'created_at' not found, using simplified query")
        query = """
        SELECT
            user_id,
            AVG(mio_sensor_data) as avg_sensor_data,
            AVG(battery_level) as avg_battery_level,
            COUNT(*) as total_readings,
            NOW() as first_reading,
            NOW() as last_reading
        FROM bionicpro_table
        GROUP BY user_id
        """
    
    df_telemetry = telemetry_hook.get_pandas_df(query)
    df_telemetry.to_csv('/tmp/telemetry_data_extract.csv', index=False)
    
    return f"Extracted telemetry for {len(df_telemetry)} users"

def transform_and_load():
    df_crm = pd.read_csv('/tmp/crm_data_extract.csv')
    df_telemetry = pd.read_csv('/tmp/telemetry_data_extract.csv')

    df_merged = pd.merge(
        df_crm,
        df_telemetry,
        on='user_id',
        how='left'
    )

    df_merged['data_quality_score'] = df_merged['total_readings'].apply(
        lambda x: 'HIGH' if x > 100 else 'MEDIUM' if x > 10 else 'LOW'
    )
    
    df_merged['battery_health'] = df_merged['avg_battery_level'].apply(
        lambda x: 'GOOD' if x > 80 else 'WARNING' if x > 50 else 'CRITICAL'
    )
    
    df_merged['etl_timestamp'] = datetime.now()
    df_merged['load_date'] = datetime.now().date()

    olap_hook = PostgresHook(postgres_conn_id='olap_connection')
    engine = create_engine(olap_hook.get_uri().replace('postgresql+psycopg2', 'postgresql'))

    df_merged.to_sql(
        'customer_telemetry_mart',
        engine,
        if_exists='append',
        index=False,
        method='multi'
    )
    
    return f"Loaded {len(df_merged)} records to OLAP mart"

def create_olap_mart():
    olap_hook = PostgresHook(postgres_conn_id='olap_connection')
    
    create_table_sql = """
    DROP TABLE IF EXISTS customer_telemetry_mart CASCADE;

    CREATE TABLE customer_telemetry_mart (
        mart_id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        customer_name VARCHAR(255),
        customer_email VARCHAR(255),
        registration_date DATE,
        subscription_type VARCHAR(50),
        region VARCHAR(100),
        account_status VARCHAR(50),
        avg_sensor_data NUMERIC(18,2),
        avg_battery_level NUMERIC(18,2),
        total_readings INTEGER,
        first_reading TIMESTAMP,
        last_reading TIMESTAMP,
        data_quality_score VARCHAR(20),
        battery_health VARCHAR(20),
        etl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        load_date DATE
    );

    CREATE INDEX idx_ctm_user_id ON customer_telemetry_mart(user_id);
    CREATE INDEX idx_ctm_region ON customer_telemetry_mart(region);
    CREATE INDEX idx_ctm_load_date ON customer_telemetry_mart(load_date);
    CREATE INDEX idx_ctm_account_status ON customer_telemetry_mart(account_status);
    """
    
    olap_hook.run(create_table_sql)
    return "OLAP mart created successfully"

with DAG('crm_olap_etl_dag',
         default_args=default_args,
         schedule_interval='0 2 * * *',
         catchup=False,
         max_active_runs=1) as dag:
    
    create_mart_table = PythonOperator(
        task_id='create_olap_mart',
        python_callable=create_olap_mart
    )
    
    extract_crm = PythonOperator(
        task_id='extract_crm_data',
        python_callable=extract_crm_data
    )
    
    extract_telemetry = PythonOperator(
        task_id='extract_telemetry_data',
        python_callable=extract_telemetry_data
    )
    
    transform_load = PythonOperator(
        task_id='transform_and_load',
        python_callable=transform_and_load
    )

    optimize_table = PostgresOperator(
            task_id='optimize_olap_table',
            postgres_conn_id='olap_connection',
            sql="""

            ANALYZE customer_telemetry_mart;

            CREATE MATERIALIZED VIEW IF NOT EXISTS daily_customer_metrics AS
            SELECT
                load_date,
                region,
                subscription_type,
                COUNT(DISTINCT user_id) as active_customers,
                AVG(avg_sensor_data) as avg_sensor_all,
                AVG(avg_battery_level) as avg_battery_all,
                SUM(CASE WHEN battery_health = 'CRITICAL' THEN 1 ELSE 0 END) as critical_battery_count
            FROM customer_telemetry_mart
            GROUP BY load_date, region, subscription_type;

            CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_metrics
            ON daily_customer_metrics (load_date, region, subscription_type);

            REFRESH MATERIALIZED VIEW CONCURRENTLY daily_customer_metrics;
            """
        )

    create_mart_table >> [extract_crm, extract_telemetry] >> transform_load >> optimize_table
