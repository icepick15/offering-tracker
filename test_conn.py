from sqlalchemy import create_engine

DB_URI = "mysql+pymysql://postgres:Workpaid00@db.nuwpgnynkprgnzokrlgi.supabase.co:5432/postgres"

# Create an engine and test the connection
engine = create_engine(DB_URI)

try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Error: {e}")
