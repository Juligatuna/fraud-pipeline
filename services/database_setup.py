from sqlalchemy import create_engine, text

engine = create_engine('postgresql://admin:password@localhost:5433/fraud_dw')

def setup_table():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id UUID PRIMARY KEY,
                customer_id INT,
                timestamp TIMESTAMP,
                amount FLOAT,
                country TEXT,
                merchant TEXT,
                fraud INT
            )
        """))
    print("Table 'transactions' created successfully on port 5433")

if __name__ == "__main__":
    setup_table()

