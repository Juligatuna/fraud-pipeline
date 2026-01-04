from sqlalchemy import create_engine

def test_connection():
    engine = create_engine('postgresql://admin:password@localhost:5433/fraud_dw')
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("Database connection successful!")
            print(f"Result: {result.fetchone()}")
    except Exception as e:
        print(f"Database connection failed: {e}")

# Call the function
test_connection()