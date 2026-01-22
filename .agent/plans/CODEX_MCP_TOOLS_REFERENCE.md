Codex용 핵심 정보

# Tavily MCP Server (전역 설정 완료)
Server: tavily
Path: /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/tavily-mcp/build/index.js
API Key: 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
Status: ✅ Ready to use

Codex 실행 시:
# Tavily MCP 서버 시작 (API 키 포함)
import subprocess
import os

process = subprocess.Popen(
    [
        "/home/palantir/.nvm/versions/node/v24.12.0/bin/node",
        "/home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/tavily-mcp/build/index.js"
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    env={
        **os.environ,
        "TAVILY_API_KEY": "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"
    }
)
