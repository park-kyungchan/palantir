
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON, MetaData, Table
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import os

# Database Path - leveraging the existing Orion artifacts directory
DB_PATH = os.path.abspath("/home/palantir/.agent/orion_ontology.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

metadata = MetaData()

# The Universal Object Table (Phonograph Pattern)
# Instead of one table per type, we use a document-store pattern for flexibility,
# backed by indices for performance.
objects_table = Table(
    "objects",
    metadata,
    Column("id", String, primary_key=True),  # UUIDv7
    Column("type", String, index=True, nullable=False),  # e.g., 'Server', 'Incident'
    Column("version", Integer, default=1),  # Optimistic Locking
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
    Column("data", JSON, nullable=False),  # The full Pydantic dump
    Column("fts_content", Text, nullable=True)  # Flattened text for FTS5 search
)

# Initialize Engine
# Enable Write-Ahead Logging (WAL) for concurrency
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)

def init_db():
    """Idempotent initialization of the database schema."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Enable WAL mode explicitly
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        
    metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
