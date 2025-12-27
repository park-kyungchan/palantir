from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, JSON, DateTime, Text
from sqlalchemy.orm import sessionmaker
import os

DB_PATH = "/home/palantir/orion-orchestrator-v2/data/ontology.db"
# Ensure directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

metadata = MetaData()

objects_table = Table(
    "objects",
    metadata,
    Column("id", String, primary_key=True, index=True),
    Column("type", String, index=True),
    Column("version", Integer, default=1),
    Column("created_at", DateTime),
    Column("updated_at", DateTime),
    Column("data", JSON, nullable=False),
    Column("fts_content", Text, default="")
)

def init_db():
    metadata.create_all(bind=engine)
