
import asyncio
import sys
import os

# Ensure V3 path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.client import FoundryClient
from scripts.llm.ollama_client import HybridRouter, OllamaClient
from scripts.relay.queue import RelayQueue

class OrionRuntime:
    """
    The V3 Semantic OS Kernel.
    Replaces the old 'loop.py'.
    """
    def __init__(self):
        self.client = FoundryClient()
        self.router = HybridRouter()
        self.llm = OllamaClient()
        self.relay = RelayQueue()
        self.running = True
        print("[Orion V3] Semantic OS Kernel Booting...")

    async def start(self):
        print("[Orion V3] Online. Waiting for Semantic Signals...")
        # Conceptual Event Loop
        while self.running:
            # 1. Check Relay Queue
            task_payload = self.relay.dequeue()
            if task_payload:
                print(f"[Kernel] Processing Relay Task: {task_payload['id']}")
                await self._process_task_cognitive(task_payload)
                self.relay.complete(task_payload['id'], "Processed by V3 Kernel")
            
            # 2. Check Proposals (HITL Worker)
            # In a real system, this would query Propoal.where(status='approved')
            # Stub logic:
            # approved_proposals = self.client.ontology.objects.Proposal.where(status="approved")
            # for p in approved_proposals:
            #     execute_action(p)
                
            await asyncio.sleep(1)

    def shutdown(self):
        self.running = False

    async def _process_task_cognitive(self, task_payload):
        """
        Cognitive Consumption: LLM Analysis -> Ontology Creation.
        """
        prompt = task_payload['prompt']
        print(f"   [Kernel] 🧠 Thinking... (Analyzing: '{prompt[:30]}...')")
        
        # 1. Ask LLM for Plan
        try:
            plan = await self.llm.generate(prompt, json_schema={"plan": []})
            print(f"   [Kernel] 🐛 Debug: LLM returned plan: {plan}")
        except Exception as e:
            print(f"   [Kernel] ❌ LLM Generation Failed: {e}")
            plan = {"plan": []}

        # 2. Iterate and Create Objects
        if "plan" in plan and isinstance(plan["plan"], list):
            for step in plan["plan"]:
                title = step.get("title", "Untitled")
                prio = step.get("priority", "medium")
                action = step.get("action", "generic")
                
                # A. Create Task Object
                # (Stub: In real system, client.ontology.objects.Task.create(...))
                print(f"   [Kernel] ✨ Created Task: {title} ({prio})")
                
                # B. Create Proposal (for hazardous actions)
                if action == "deploy_production":
                    from scripts.ontology.objects.proposal import Proposal
                    proposal = Proposal(
                        action_type=action, 
                        parameters_json='{}', 
                        created_by_id='kernel', 
                        status='pending'
                    )
                    print(f"   [Kernel] 🛡️  Created Proposal for '{action}': {proposal.id} (Status: {proposal.status})")
        else:
            print("   [Kernel] ⚠️  No structured plan returned.")
        print("[Orion V3] Shutting down.")

if __name__ == "__main__":
    runtime = OrionRuntime()
    try:
        asyncio.run(runtime.start())
    except KeyboardInterrupt:
        runtime.shutdown()
