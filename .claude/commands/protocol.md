---
description: Execute ODA 3-Stage Protocol directly
allowed-tools: Bash, Read, TodoWrite
argument-hint: <protocol_name> <target_path>
---

# /protocol Command

Execute an ODA protocol with full 3-Stage governance.

## Arguments
$1 - Protocol name (audit, planning, execution)
$2 - Target path (default: current directory)

## Execution

```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate 2>/dev/null

python -c "
import asyncio
from scripts.claude.protocol_adapter import ODAProtocolAdapter, PROTOCOL_REGISTRY

async def run():
    protocol_name = '$1' or 'audit'
    target_path = '$2' or '.'

    protocol_cls = PROTOCOL_REGISTRY.get(protocol_name)
    if not protocol_cls:
        print(f'Unknown protocol: {protocol_name}')
        print(f'Available: {list(PROTOCOL_REGISTRY.keys())}')
        return

    adapter = ODAProtocolAdapter(
        protocol=protocol_cls(),
        target_path=target_path,
        session_id='cli_session',
    )

    print(f'Executing {protocol_name} protocol on {target_path}')

    result_a = await adapter.execute_stage_a()
    print(f'Stage A: {\"PASS\" if result_a.passed else \"FAIL\"} - {result_a.message}')

    if result_a.passed:
        result_b = await adapter.execute_stage_b()
        print(f'Stage B: {\"PASS\" if result_b.passed else \"FAIL\"} - {result_b.message}')

        if result_b.passed:
            result_c = await adapter.execute_stage_c()
            print(f'Stage C: {\"PASS\" if result_c.passed else \"FAIL\"} - {result_c.message}')

asyncio.run(run())
"
```

## Example
```
/protocol audit scripts/ontology/
/protocol planning .
```
