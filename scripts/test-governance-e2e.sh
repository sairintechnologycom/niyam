#!/usr/bin/env bash
set -euo pipefail

echo "== Niyam Governance E2E Test =="

TEST_ROOT="$(pwd)"
APP_DIR="test-fixtures/apps/risky-vibe-app"
REPORT_DIR=".niyam/reports"
mkdir -p "$REPORT_DIR"

# Clean up any existing state to ensure clean run
python3 -c "import os, shutil; [os.remove(f) for f in ['.niyam/mcp-registry.json'] if os.path.exists(f)]; [shutil.rmtree(d, ignore_errors=True) for d in ['.niyam/logs', '$REPORT_DIR']]"
mkdir -p "$REPORT_DIR"

# Ensure we have a valid niyam configuration for guard/cost log testing
mkdir -p .niyam
if [ ! -f .niyam/niyam.yaml ]; then
  cat <<EOF > .niyam/niyam.yaml
version: 0.1.0
project_name: e2e-test-project
profile: fullstack
runtimes:
  - claude
EOF
fi

echo "1. Check CLI help"
uv run niyam --help
uv run niyam scan --help
uv run niyam guard --help
uv run niyam mcp --help
uv run niyam cost --help
uv run niyam evidence --help

echo "2. Run scan"
uv run niyam scan "$APP_DIR" \
  --profile startup \
  --output json > "$REPORT_DIR/latest-scan.json" || [ $? -eq 2 ]
test -f "$REPORT_DIR/latest-scan.json"

echo "3. Generate evidence from scan"
uv run niyam evidence generate \
  --from "$REPORT_DIR/latest-scan.json" \
  --format markdown \
  --output "$REPORT_DIR/scan-evidence.md"
test -f "$REPORT_DIR/scan-evidence.md"

echo "4. Run guard observe command"
uv run niyam guard run -- echo "hello from guard"
test -f ".niyam/logs/guard-actions.jsonl"

echo "5. Register MCP tools"
uv run niyam mcp register filesystem \
  --type mcp_server \
  --risk high \
  --approved false
uv run niyam mcp register docs-search \
  --type mcp_server \
  --risk medium \
  --approved true
uv run niyam mcp list
uv run niyam mcp risk-report
test -f ".niyam/mcp-registry.json"

echo "6. Log cost event"
uv run niyam cost log \
  --tool claude-code \
  --model claude-sonnet \
  --input-tokens 10000 \
  --output-tokens 2500 \
  --task "e2e governance test"
uv run niyam cost summary
test -f ".niyam/logs/cost-events.jsonl"

echo "7. Generate integrated evidence"
uv run niyam evidence generate \
  --from "$REPORT_DIR/latest-scan.json" \
  --include scan,guard,mcp,cost \
  --format markdown \
  --output "$REPORT_DIR/integrated-evidence.md"
test -f "$REPORT_DIR/integrated-evidence.md"

echo "8. Validate integrated evidence content"
grep -i "executive summary" "$REPORT_DIR/integrated-evidence.md"
grep -i "readiness" "$REPORT_DIR/integrated-evidence.md"
grep -i "mcp" "$REPORT_DIR/integrated-evidence.md"
grep -i "cost" "$REPORT_DIR/integrated-evidence.md"

echo "9. Run full test suite"
uv run pytest tests/test_governance_integration.py -v

echo "== E2E Test Passed =="
