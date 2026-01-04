from airflow import DAG
try:
    from airflow.providers.standard.operators.python import PythonOperator
except ImportError:
    from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import psycopg2

BASE_PATH = "/home/julius-irungu/Desktop/Projects/fraud-pipeline"

def clean():
    """Clean data and prepare CSV for PostgreSQL COPY"""
    df = pd.read_parquet(f"{BASE_PATH}/data/raw.parquet")
    df = df.dropna().drop_duplicates()
    
    
    if 'merchant' in df.columns:
        df['merchant'] = df['merchant'].str.replace(',', '', regex=False)
    
    
    if 'transaction_id' in df.columns:
        df['transaction_id'] = df['transaction_id'].astype(str)
    
    
    required_columns = ['transaction_id', 'customer_id', 'timestamp', 'amount', 'country', 'merchant', 'fraud']
    df = df[required_columns]
    
    
    df.to_parquet(f"{BASE_PATH}/data/cleaned.parquet")
    
   
    df.to_csv(
        f"{BASE_PATH}/data/warehouse_staging.csv", 
        index=False
    )
    
    print(f"Cleaned {len(df)} rows. CSV prepared for PostgreSQL COPY.")

def train_model():
    """Train fraud detection model"""
    df = pd.read_parquet(f"{BASE_PATH}/data/cleaned.parquet")
    
    if len(df) < 500:
        print("Not enough data. Skipping training.")
        return
    
    X = df[["amount"]]
    y = df["fraud"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    joblib.dump(model, f"{BASE_PATH}/model/fraud.pkl")
    print(f"Model trained on {len(X_train)} samples and saved.")

def load_to_postgres():
    """Load data to PostgreSQL using COPY command"""
    import psycopg2
    import os
    
    csv_path = f"{BASE_PATH}/data/warehouse_staging.csv"
    
    if not os.path.exists(csv_path):
        print(f"ERROR: CSV file not found at {csv_path}")
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    print(f"Loading data from {csv_path}")
    
    try:
        
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            dbname="fraud_dw",
            user="admin",
            password="password"
        )
        cur = conn.cursor()
        
        
        cur.execute("TRUNCATE transactions;")
        print("Table truncated")
        
       
        with open(csv_path, 'r') as f:
            cur.copy_expert("""
                COPY transactions(transaction_id, customer_id, timestamp, amount, country, merchant, fraud) 
                FROM STDIN WITH CSV HEADER
            """, f)
        
        conn.commit()
        
        # Verify load
        cur.execute("SELECT COUNT(*) FROM transactions;")
        count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        print(f"SUCCESS: {count} rows loaded to PostgreSQL")
        
    except Exception as e:
        print(f"ERROR loading to PostgreSQL: {e}")
        raise

with DAG(
    "fraud_pipeline_v3",
    start_date=datetime(2026, 1, 1),
    schedule="*/5 * * * *",
    catchup=False,
) as dag:
    
    clean_task = PythonOperator(task_id="clean_data", python_callable=clean)
    train_task = PythonOperator(task_id="train_model", python_callable=train_model)
    load_task = PythonOperator(task_id="load_to_postgres", python_callable=load_to_postgres)

    clean_task >> train_task >> load_task