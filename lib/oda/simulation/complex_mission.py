
import asyncio
import uuid
import sys
import os

# Setup Path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from lib.oda.runtime.kernel import OrionRuntime
from lib.oda.relay.queue import RelayQueue
from lib.oda.ontology.storage import ProposalRepository, initialize_database

async def run_complex_simulation():
    print("🚀 [Simulation] Starting 'Mission Critical' Complex Task Scenario...")
    
    # 1. Setup Infrastructure
    db = await initialize_database()
    queue = RelayQueue()
    kernel = OrionRuntime()
    kernel.repo = ProposalRepository(db)
    kernel.relay = queue
    
    # 2. User User Ingests Complex Request
    complex_prompt = """
    OBJECTIVE: Deploy a new Checkout Microservice.
    REQUIREMENTS:
    1. Create a Python Service (FastAPI).
    2. Setup PostgreSQL Database.
    3. Configure Stripe Webhook.
    4. Deploy to Kubernetes (Production).
    """
    
    task_id = await queue.enqueue(complex_prompt) # This triggers the "Router -> Relay" path conceptually
    print(f"📨 [User] Submitted Request ID: {task_id}")
    print(f"📝 Prompt: {complex_prompt.strip()[:50]}...")
    
    # 3. Start Kernel (in background logic) to process it
    # We will run the kernel for a few cycles to let it consume
    print("\n⚙️ [Kernel] Booting up to consume task...")
    
    # Run kernel process_loop once directly for test deterministic behavior
    # (Extracting logic from start() for granular control)
    item = await queue.dequeue()
    if item:
        print(f"   [Kernel] Dequeued Item: {item['id']}")
        
        # --- THE TEST: Call the NEW Cognitive Method ---
        # accessing private method for verification
        await kernel._process_task_cognitive(item)
        print("   [Kernel] Task marked Complete.")
    else:
        print("   [Kernel] No task found!")

    print("\n🏁 [Simulation] Scenario Finished.")

if __name__ == "__main__":
    asyncio.run(run_complex_simulation())
