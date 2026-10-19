"""Database models and connection for PostgreSQL."""
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in .env file")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Run(Base):
    """Model for tracking agent runs."""
    __tablename__ = "runs"
    
    id = Column(String, primary_key=True)
    version = Column(String, nullable=False)  # "v1" or "v2"
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_answers = Column(Integer)
    extraction_f1 = Column(Float)
    classification_macro_f1 = Column(Float)
    combined_f1 = Column(Float)


class Answer(Base):
    """Model for storing answer records."""
    __tablename__ = "answers"
    
    id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False)
    answer_id = Column(String, nullable=False)
    brand_id = Column(String)
    model_id = Column(String)
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    """Model for storing claim predictions."""
    __tablename__ = "predictions"
    
    id = Column(String, primary_key=True)
    run_id = Column(String, nullable=False)
    answer_id = Column(String, nullable=False)
    start_char = Column(Integer)
    end_char = Column(Integer)
    quote = Column(Text)
    classification = Column(String)  # "supported", "contradicted", "unknown"
    timestamp = Column(DateTime, default=datetime.utcnow)


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
