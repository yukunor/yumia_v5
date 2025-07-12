from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base  # ← ここも絶対インポートに合わせて修正

import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
