import os
import time
import mysql.connector
import clickhouse_connect

MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
MYSQL_USER = os.getenv("MYSQL_USER", "app_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "app_password")
MYSQL_DB = os.getenv("MYSQL_DB", "app_db")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "clickhouse_password")

def get_conns():
    while True:
        try:
            m_conn = mysql.connector.connect(
                host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
            )
            ch_client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST, port=CLICKHOUSE_PORT, username="default", password=CLICKHOUSE_PASSWORD
            )
            return m_conn, ch_client
        except Exception as e:
            print(f"Waiting for services... ({e})")
            time.sleep(3)

def apply_sql_models(ch_client):
    print("Applying Staging and Marts models from /app/modeling...")
    modeling_dir = "/app/modeling"
    
    if os.path.exists(modeling_dir):
        # Sort files to ensure numbered order (01_staging before 02_marts)
        sql_files = sorted([
            os.path.join(modeling_dir, f) 
            for f in os.listdir(modeling_dir) 
            if f.endswith(".sql")
        ])
        
        for file_path in sql_files:
            print(f"Executing model file: {file_path}")
            with open(file_path, "r") as f:
                # Split SQL commands by semicolon
                sql_commands = f.read().split(";")
                for cmd in sql_commands:
                    # Clean command and remove empty comment lines
                    cleaned_cmd = "\n".join([
                        line for line in cmd.splitlines() 
                        if not line.strip().startswith("--")
                    ]).strip()
                    
                    if cleaned_cmd:
                        ch_client.command(cleaned_cmd)
                        
    print("Data modeling complete!")

def run_etl():
    m_conn, ch_client = get_conns()
    m_cursor = m_conn.cursor(dictionary=True)

    ch_client.command("CREATE DATABASE IF NOT EXISTS raw;")

    tables = {
        "users": "user_id Int32, signup_date DateTime, city Nullable(String), acquisition_channel String",
        "restaurants": "restaurant_id Int32, name String, city String, category String",
        "products": "product_id Int32, restaurant_id Int32, name String, price Float64",
        "orders": "order_id Int32, user_id Int32, restaurant_id Int32, order_timestamp DateTime, status String, total Float64, platform String, basket_size Int32",
        "order_items": "item_id Int32, order_id Int32, product_id Int32, quantity Int32, price Float64",
        "experiment_assignments": "assignment_id Int32, user_id Int32, experiment_name String, variant String, assigned_at DateTime",
        "experiment_exposures": "exposure_id Int32, user_id Int32, experiment_name String, exposed_at DateTime"
    }

    primary_keys = {
        "users": "user_id",
        "restaurants": "restaurant_id",
        "products": "product_id",
        "orders": "order_id",
        "order_items": "item_id",
        "experiment_assignments": "assignment_id",
        "experiment_exposures": "exposure_id"
    }

    for t_name, schema in tables.items():
        print(f"Extracting {t_name} from MySQL to ClickHouse raw...")
        pk = primary_keys[t_name]
        
        ch_client.command(f"""
            CREATE TABLE IF NOT EXISTS raw.{t_name} ({schema})
            ENGINE = ReplacingMergeTree()
            ORDER BY ({pk});
        """)
        
        m_cursor.execute(f"SELECT * FROM {t_name}")
        rows = m_cursor.fetchall()
        
        if rows:
            ch_client.command(f"TRUNCATE TABLE raw.{t_name};")
            col_names = list(rows[0].keys())
            data_matrix = [[row[col] for col in col_names] for row in rows]
            ch_client.insert(f"raw.{t_name}", data_matrix, column_names=col_names)

    print("Raw load complete.")
    m_cursor.close()
    m_conn.close()

    apply_sql_models(ch_client)

if __name__ == "__main__":
    run_etl()