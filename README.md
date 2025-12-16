Задача 2

docker-compose up -d

Настройка Airflow через Web UI
Откройте Airflow:
Перейдите по адресу: http://localhost:8081

Логин: admin
Пароль: admin

Создайте подключения в интерфейсе Airflow:

Admin → Connections

Подключение 1: CRM Database

Connection Id: crm_connection
Connection Type: Postgres
Host: postgres
Schema: crm_database
Login: airflow
Password: airflow
Port: 5432

Подключение 2: OLAP Database
Connection Id: olap_connection
Connection Type: Postgres
Host: postgres
Schema: olap_database
Login: airflow
Password: airflow
Port: 5432

Подключение 3: Для существующего DAG
Connection Id: write_to_postgres
Connection Type: Postgres
Host: postgres
Schema: airflow
Login: airflow
Password: airflow
Port: 5432

Создайте базу OLAP:

docker-compose exec postgres psql -U airflow -d airflow

Выполните:
CREATE DATABASE olap_database;
GRANT ALL PRIVILEGES ON DATABASE olap_database TO airflow;
\q

docker-compose exec postgres psql -U airflow -d airflow

Выполните:
CREATE DATABASE crm_database;
GRANT ALL PRIVILEGES ON DATABASE crm_database TO airflow;
\q

Инициализация тестовых данных для CRM данных:
Создайте тестовую таблицу в БД:

docker-compose exec postgres psql -U airflow -d crm_database -c "
CREATE TABLE IF NOT EXISTS customers (
user_id BIGINT PRIMARY KEY,
customer_name VARCHAR(255),
customer_email VARCHAR(255),
registration_date DATE,
subscription_type VARCHAR(50),
region VARCHAR(100),
account_status VARCHAR(50),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO customers (user_id, customer_name, customer_email, registration_date, subscription_type, region, account_status) VALUES
(101, 'Иван Петров', 'ivan@example.com', '2024-01-15', 'premium', 'Moscow', 'active'),
(102, 'Мария Сидорова', 'maria@example.com', '2024-02-20', 'basic', 'Saint-Petersburg', 'active'),
(103, 'Алексей Иванов', 'alex@example.com', '2024-03-10', 'enterprise', 'Novosibirsk', 'suspended');
"

Откройте DAG http://localhost:8081 и найдите DAG crm_olap_etl_dag

Переключите тумблер в положение "On"

Проверка результатов
Проверьте данные в OLAP витрине:

docker-compose exec postgres psql -U airflow -d olap_database -c "
SELECT * FROM customer_telemetry_mart LIMIT 5;
"

docker-compose exec postgres psql -U airflow -d olap_database -c "
SELECT * FROM daily_customer_metrics;
"

Результат:
https://disk.yandex.ru/d/E5dYRQcxGqTwUQ