# test_db_connection.py
from sqlalchemy import create_engine

DATABASE_URI = 'postgresql://cbf:cbf2024@68.183.186.239:5432/cbf2024'
engine = create_engine(DATABASE_URI)

try:
    with engine.connect() as connection:
        result = connection.execute("SELECT 1")
        print("Database connection successful:", result.fetchone())
except Exception as e:
    print("Database connection failed:", str(e))
