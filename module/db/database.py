import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from module.db.models import Base   # ← 相対でなく絶対に統一


DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
