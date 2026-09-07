import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()  # reads DB_HOST, DB_PORT, etc. from your .env file

host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}")

with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
    ))
    print("Connected successfully! Tables found in 'public' schema:")
    for row in result:
        print(" -", row[0])