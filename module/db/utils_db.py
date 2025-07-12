from .database import SessionLocal
from .models import Message

def append_history_db(role: str, message: str):
    db = SessionLocal()
    try:
        entry = Message(role=role, message=message)
        db.add(entry)
        db.commit()
    finally:
        db.close()

def load_history_db():
    db = SessionLocal()
    try:
        return db.query(Message).order_by(Message.timestamp.asc()).all()
    finally:
        db.close()
