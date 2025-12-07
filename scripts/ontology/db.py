
import os
from sqlalchemy import create_engine, Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# --- Configuration ---
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AGENT_DIR = os.path.join(WORKSPACE_ROOT, ".agent")
if not os.path.exists(AGENT_DIR):
    os.makedirs(AGENT_DIR)
    
DB_PATH = os.path.join(AGENT_DIR, "orion_ontology.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# --- SQLAlchemy Setup ---
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

class ObjectTable(Base):
    """
    Universal Table for all OrionObjects.
    Uses JSON column for flexible schema storage.
    """
    __tablename__ = "objects"

    id = Column(String, primary_key=True, index=True)
    type = Column(String, index=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    # The Payload
    data = Column(JSON)
    
    # FTS Optimization (Redundant text for searching)
    fts_content = Column(Text, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)
