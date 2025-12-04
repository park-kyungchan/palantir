# Orion Global Makefile
# Orchestrates the entire workspace using scripts/orion

.PHONY: init audit research test-math

# --- Orion Core ---
init:
	@python3 scripts/orion init

# --- Workflows ---
audit:
	@echo "🔍 [Orion] Dispatching Code Audit..."
	@python3 scripts/orion dispatch "Audit Codebase for Best Practices" "Auditor" "coding/"

research:
	@echo "📚 [Orion] Dispatching Deep Research..."
	@python3 scripts/orion dispatch "Research Latest Tech Stack" "Researcher"

# --- Project Shortcuts ---
test-math:
	@echo "🧪 Testing Math Project..."
	@cd math && make test-all
