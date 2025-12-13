# MCP Tooling Governance (ODA, Multi-Agent)

## Problem Statement (React Error #185)

VS Code/Antigravity IDE에서 **설정된 MCP 서버가 시작되지 않거나 연결 실패**하면, IDE가 연결을 무한 재시도하면서 React state 업데이트가 폭주해 `React Error #185 (Maximum update depth exceeded)`가 발생할 수 있습니다.

이 레포/환경에서는 특히 다음 케이스가 트리거가 됩니다:
- `github-mcp-server`가 **Docker 기반**일 때: 사용자 세션이 Docker 소켓(`/var/run/docker.sock`)에 접근 권한이 없거나 Docker 데몬이 내려가 있어 MCP 서버 시작 실패 → IDE 재시도 루프
- `github-mcp-server`가 **`npx` 기반**일 때: 패키지 미설치/네트워크 제한으로 실행 실패 → IDE 재시도 루프

ODA 관점에서 이는 “Ontology 자체 버그”라기보다, **ODA가 (의도대로) 외부 Kinetic Capability(MCP server)를 참조**하는데 그 capability가 런타임에서 불능인 상태가 방치되면서 IDE 버그를 촉발하는 형태입니다. 따라서 해결은 “서버 불능 상태를 사전에 탐지/차단”하고 “툴 정의를 단일 소스에서 일관되게 관리”하는 쪽이 효과적입니다.

---

## Single Source of Truth: Canonical MCP Registry

LLM/에이전트가 여러 개(Claude/Codex/Gemini)여도 **MCP 서버 정의는 1곳에서만 관리**합니다.

- Canonical registry: `/home/palantir/.agent/mcp/registry.json`
- Audit log (no secret values): `/home/palantir/.agent/logs/mcp_audit.jsonl`

보안 원칙:
- 레지스트리에는 `env` 값을 저장하지 않고 `envKeys`만 저장합니다.
- 동기화 시에도 기존 설정 파일에 이미 존재하는 `env` 값만 보존하고, 새로 주입하지 않습니다.

---

## Managed Targets (Sync)

레지스트리에서 각 에이전트/클라이언트 설정으로 “동일한 command/args”를 전파합니다.

- Antigravity IDE (Gemini): `/home/palantir/.gemini/antigravity/mcp_config.json`
  - 주의: IDE React #185 회피를 위해 여기서 **실패 서버 disable**이 특히 중요합니다.
- Claude Code CLI: `/home/palantir/.claude.json` (project scoped `projects["/home/palantir"].mcpServers`)
- Codex CLI: 별도 MCP 설정 파일이 없을 수 있으나, Codex도 레지스트리를 기준으로 “사용 가능한 도구”를 판단/가이드합니다.

ID 매핑:
- Registry의 `github` ↔ Antigravity 설정의 `github-mcp-server`

---

## 운영 워크플로우 (LLM-Independent)

모든 에이전트는 아래 stdlib-only 스크립트를 동일하게 사용할 수 있습니다:

- Registry/Sync: `orion-orchestrator-v2/scripts/mcp_manager.py`
- Preflight(IDE 루프 완화): `orion-orchestrator-v2/scripts/mcp_preflight.py`

### 1) 현재 상태를 레지스트리로 초기화

```bash
python3 orion-orchestrator-v2/scripts/mcp_manager.py init-registry --write
```

### 2) 레지스트리 → 각 에이전트 설정으로 동기화

```bash
python3 orion-orchestrator-v2/scripts/mcp_manager.py sync --write
```

### 3) IDE 안정화 Preflight (실패 서버 자동 disable)

```bash
python3 orion-orchestrator-v2/scripts/mcp_preflight.py --auto-disable-failed --write
```

---

## GitHub MCP: Docker → Native 권장

IDE 안정성/권한 문제(Docker 소켓) 회피를 위해 `github-mcp-server`는 native binary 사용을 권장합니다.

```bash
python3 orion-orchestrator-v2/scripts/mcp_manager.py install-github --tag latest --install-path /home/palantir/.local/bin/github-mcp-server
python3 orion-orchestrator-v2/scripts/mcp_manager.py set-github-native --write --install-path /home/palantir/.local/bin/github-mcp-server
```

이후 Antigravity/Claude 설정이 레지스트리 기준으로 업데이트되어 Docker 의존성이 제거됩니다.
