from typing import List
from lib.digital_twin.schema import DigitalTwin, Block
from lib.knowledge.schema import ActionDatabase, ActionDefinition

class ActionTableParser:
    """
    Parses 'ActionTable' Digital Twin content into a structured ActionDatabase.
    """
    def parse(self, twin: DigitalTwin) -> ActionDatabase:
        db = ActionDatabase()
        
        for page in twin.pages:
            for block in page.blocks:
                if block.type == "table":
                    self._parse_table(block, db)
                    
        return db

    def _parse_table(self, block: Block, db: ActionDatabase):
        rows = block.content.table_data
        if not rows:
            return
            
        # Heuristic: Check headers
        headers = [h.strip().lower() for h in rows[0]]
        
        # Expected: Action ID | ParameterSet ID | Description | ...
        # Allow fuzzy matching if Vision wasn't perfect
        try:
            # Find column indices
            # Note: actual headers might be 'Action ID', 'ParameterSet ID'
            idx_action = -1
            idx_param = -1
            idx_desc = -1
            
            for i, h in enumerate(headers):
                if "action id" in h:
                    idx_action = i
                elif "parameterset" in h:
                    idx_param = i
                elif "description" in h:
                    idx_desc = i
            
            if idx_action == -1:
                return # Not an action table

            # Iterate Data Rows
            for row in rows[1:]:
                if len(row) <= idx_action:
                    continue
                    
                action_id = row[idx_action].strip()
                if not action_id:
                    continue
                
                param_set = row[idx_param].strip() if idx_param != -1 and len(row) > idx_param else None
                desc = row[idx_desc].strip() if idx_desc != -1 and len(row) > idx_desc else None
                
                # Cleanup symbols from PDF
                # Symbol '-' means None
                # Symbol '+' means Future
                # Symbol '*' means ...
                
                requires_creation = False
                run_blocked = False
                
                if param_set:
                    if param_set == "-" or param_set == "+":
                        param_set = None
                    elif param_set.endswith("*"):
                        param_set = param_set.rstrip("*")
                        run_blocked = True # Assumption based on Page 1 legend? Or requires specific creation?
                        # Legend says '*' means 'HwpCtrl.Run impossible' -> needs 'CreateAction'
                
                action_def = ActionDefinition(
                    action_id=action_id,
                    parameter_set_id=param_set,
                    description_ko=desc,
                    run_blocked=run_blocked
                )
                
                db.add_action(action_def)
                
        except Exception as e:
            print(f"Error parsing table block {block.id}: {e}")
