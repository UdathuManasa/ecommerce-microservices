from sqlalchemy import create_engine

# Replace with your actual credentials if different
DATABASE_URL = "mysql+pymysql://ecommerce_user:Manasa123@localhost:3306/ecommerce_auth"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as connection:
        print(" SUCCESS: Database connection established successfully!")
except Exception as e:
    print(f" CONNECTION FAILED:\n{e}")