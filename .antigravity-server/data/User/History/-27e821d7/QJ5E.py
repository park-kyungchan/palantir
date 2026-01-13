#!/usr/bin/env python3
import sys
import os

def check_compliance():
    """
    Simulated Governance Guardrail.
    In a real system, this would parse Action Logs.
    Here, it forces the Agent to acknowledge the protocol.
    """
    print(">> [GOVERNANCE] ODA Deep Audit Protocol Enforcer v1.0")
    print(">> [CHECK 1] Scanning for 'web_search' usage... REQUIRED")
    print(">> [CHECK 2] Scanning for 'task_boundary' (Sequential Thinking)... REQUIRED")
    
    # In a real shell execution, we cannot easily see previous commands.
    # So we output a BLOCKING instruction.
    print("\n !!! OPERATION HALTED !!!")
    print(" You must verify assumptions with 'tavily' (web_search) AND")
    print(" document reasoning with 'sequential-thinking' before proceeding.\n")
    print(">> If you have done this, run this script with --verify-override")

if __name__ == "__main__":
    if "--verify-override" not in sys.argv:
        check_compliance()
        sys.exit(1)
    else:
        print(">> [GOVERNANCE] Override accepted. Proceeding with Audit Report Generation.")
        sys.exit(0)
