
"""
Governance Administration Tool (ODA v3.5).
Provides CLI access to the Proposal System via ProposalRepository.
"""

import asyncio
import sys
import logging
from typing import Optional
import argparse

# ODA Imports
from lib.oda.ontology.storage import ProposalRepository, initialize_database
from lib.oda.ontology.objects.proposal import ProposalStatus

logging.basicConfig(level=logging.INFO, format="[Governance] %(message)s")
logger = logging.getLogger("Governance")

async def list_proposals(status: Optional[str] = None):
    db = await initialize_database()
    repo = ProposalRepository(db)
    
    filter_status = ProposalStatus(status) if status else ProposalStatus.PENDING
    
    proposals = await repo.find_by_status(filter_status)
    if not proposals:
        print(f"No proposals found with status: {filter_status}")
        return

    print(f"\nFound {len(proposals)} {filter_status} proposals:")
    for p in proposals:
        print(f"  [{p.id}] {p.action_type} (Priority: {p.priority})")
        print(f"      Summary: {str(p.payload)[:100]}...")

async def approve_proposal(proposal_id: str, reviewer: str):
    db = await initialize_database()
    repo = ProposalRepository(db)
    
    try:
        # Check if exists
        p = await repo.find_by_id(proposal_id)
        if not p:
            print(f"Proposal {proposal_id} not found.")
            return

        stmt = await repo.update_status(
            proposal_id, 
            ProposalStatus.APPROVED, 
            reviewed_by=reviewer,
            review_comment="Approved via Governance CLI"
        )
        print(f"✅ Proposal {proposal_id} APPROVED by {reviewer}")
        
    except Exception as e:
        print(f"❌ Approval Failed: {e}")

async def reject_proposal(proposal_id: str, reviewer: str, reason: str):
    db = await initialize_database()
    repo = ProposalRepository(db)
    
    try:
        await repo.update_status(
            proposal_id,
            ProposalStatus.REJECTED,
            reviewed_by=reviewer,
            review_comment=reason
        )
        print(f"🚫 Proposal {proposal_id} REJECTED.")
    except Exception as e:
        print(f"❌ Rejection Failed: {e}")

async def main():
    parser = argparse.ArgumentParser(description="Orion Governance CLI")
    subparsers = parser.add_subparsers(dest="command")
    
    # List
    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", default="pending", help="Filter by status")
    
    # Approve
    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("id", help="Proposal ID")
    approve_parser.add_argument("--reviewer", default="admin", help="Reviewer ID")
    
    # Reject
    reject_parser = subparsers.add_parser("reject")
    reject_parser.add_argument("id", help="Proposal ID")
    reject_parser.add_argument("--reason", required=True, help="Rejection Reason")
    reject_parser.add_argument("--reviewer", default="admin", help="Reviewer ID")

    args = parser.parse_args()
    
    if args.command == "list":
        await list_proposals(args.status)
    elif args.command == "approve":
        await approve_proposal(args.id, args.reviewer)
    elif args.command == "reject":
        await reject_proposal(args.id, args.reviewer, args.reason)
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
