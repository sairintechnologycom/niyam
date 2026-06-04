# Niyam AI Engineering Cost Tracking (`niyam cost`)

> [!WARNING]
> The Cost Tracking module is currently **experimental**. Database structures, API estimators, and CLI properties are subject to change in upcoming releases.

Niyam includes a local **AI engineering cost tracking system** to help teams monitor, audit, and analyze token usage and model expenses incurred during AI-assisted development sessions.

---

## 1. Cost Commands

The `niyam cost` command group provides the following subcommands:

| Command | Description |
| --- | --- |
| `niyam cost log` | Records a token usage and cost event. |
| `niyam cost summary` | Renders a high-level summary of total events, tokens, and estimated cost. |
| `niyam cost report` | Outputs detailed markdown tables grouped by day, repository, task, and status. |

---

## 2. Logging Cost Events

To log a token usage event manually or programmatically:

```bash
niyam cost log \
  --tool "claude-code" \
  --model "claude-3-5-sonnet" \
  --input-tokens 12500 \
  --output-tokens 3200 \
  --task "refactor-scanner" \
  --status "success" \
  --notes "Initial refactoring task."
```

### Parameters Supported
- `--tool`: The AI client interface (e.g. `claude-code`, `codex`, `gemini`).
- `--model`: Model identifier (e.g. `claude-3-5-sonnet`, `gpt-4o`, `gemini-pro`).
- `--input-tokens`: Count of input/prompt tokens.
- `--output-tokens`: Count of output/completion tokens.
- `--task`: Name or ID of the task.
- `--status`: Execution outcome (`success`, `failed`, or `repeated`).
- `--notes`: Free-form text annotations.

---

## 3. Reporting & Auditing

Execute `niyam cost report` to render structured audit tables:

1. **Cost by Day:** Groups spending by YYYY-MM-DD.
2. **Cost by Repository:** Groups spending by local Git repository directory name.
3. **Cost by Task:** Groups spending by unique task IDs.
4. **Top Expensive Sessions:** Highlights the top 5 most expensive runs.
5. **Wasted Budget:** Quantifies the cost and count of failed or repeated runs (helping evaluate agent efficiency).

---

## 4. Local Pricing Configuration

Costs are calculated using a configurable rates table stored locally in JSON format at:
```
.niyam/pricing.json
```

It is initialized with default pricing for common model vendors. You can add or modify rates in USD per million tokens:

```json
{
  "claude-3-5-sonnet": {
    "input_cost_per_million": 3.00,
    "output_cost_per_million": 15.00
  },
  "gpt-4o": {
    "input_cost_per_million": 5.00,
    "output_cost_per_million": 15.00
  },
  "gemini-1.5-pro": {
    "input_cost_per_million": 1.25,
    "output_cost_per_million": 5.00
  }
}
```

---

## 5. Event Log Format

Events are appended locally in JSON Lines (JSONL) format to:
```
.niyam/logs/cost-events.jsonl
```

### Log Event Schema
```json
{
  "timestamp": "2026-06-04T10:45:00Z",
  "session_id": "branch-main-1234",
  "task_id": "refactor-scanner",
  "tool_name": "claude-code",
  "model": "claude-3-5-sonnet",
  "input_tokens": 12500,
  "output_tokens": 3200,
  "estimated_cost": 0.0855,
  "repo": "my-sample-app",
  "branch": "main",
  "status": "success",
  "notes": "Initial refactoring task."
}
```
No API keys or system secrets are stored inside the cost log events.
