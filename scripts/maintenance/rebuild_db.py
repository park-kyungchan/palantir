
import asyncio
import sys
import os
import logging
from sqlalchemy import text

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from scripts.ontology.storage.database import initialize_database
from scripts.ontology.storage.models import Base

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB_Rebuilder")

async def rebuild_database():
    logger.warning("🚨 INITIATING DATABASE REBUILD (DESTRUCTIVE OPERATION) 🚨")
    
    # 1. Initialize
    db = await initialize_database()
    
    # 2. Rebuild Schema
    async with db.engine.begin() as conn:
        logger.info("💥 Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("🏗️ Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    # 3. Optimization
    async with db.transaction() as session:
        logger.info("🧹 Vacuuming...")
        await session.execute(text("VACUUM"))
        
    logger.info("✅ Database Rebuild Complete.")

if __name__ == "__main__":
    confirm = input("Are you sure you want to WIPEOUT the database? (y/n): ")
    if confirm.lower() == 'y':
        asyncio.run(rebuild_database())
    else:
        print("Aborted.")
