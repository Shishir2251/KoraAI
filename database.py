import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from models import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(blind=engine, autucommit=False, autoflush=False)

Base.metadata.create_all(blind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()