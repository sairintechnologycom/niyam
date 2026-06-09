# Niyam Browser Sandbox

Niyam provides a sandboxed environment for representative browser-agent tasks. This allows agents to perform web-based operations under human supervision, with risky actions gated by approval requests.

## Architecture

The browser sandbox is designed with a pluggable backend architecture.

### BrowserBackend Interface

All browser operations are abstracted through the `BrowserBackend` interface, ensuring that the core Niyam logic remains decoupled from specific automation libraries like Playwright or Selenium.

```python
class BrowserBackend(ABC):
    def start(self, start_url: str | None) -> BrowserSession: ...
    def navigate(self, url: str) -> BrowserAction: ...
    def click(self, selector: str) -> BrowserAction: ...
    def type(self, selector: str, text: str) -> BrowserAction: ...
    def screenshot(self, output_path: Path | None) -> BrowserAction: ...
    def close(self) -> BrowserSession: ...
```

### RecorderBackend (Default)

By default, Niyam uses the `RecorderBrowserBackend`. This backend does not require any external dependencies (like Playwright) and is used for:
- Logging intended actions without execution.
- CI/CD stability.
- Testing governance and approval flows without browser overhead.

### PlaywrightBackend (Optional)

A real browser execution backend using Playwright can be enabled when the dependencies are installed and explicitly requested.

## Governance & Approvals

Browser actions are automatically classified by risk:

| Action | Default Risk | Approval Required |
| --- | --- | --- |
| `navigate` | Low | No |
| `wait` | Low | No |
| `extract` | Low | No |
| `click` | Medium | No |
| `type` | Medium / High* | If high risk |
| `submit` | High | Yes |

\* `type` actions are classified as high risk if the selector or input appears to contain sensitive information (e.g., passwords).

When a high-risk action is attempted, Niyam:
1. Suspends the action.
2. Creates a `WorkspaceApproval` request.
3. Sets the session status to `approval_required`.
4. Resumes only after a human provides an `approved` decision.

## Human Takeover

The `takeover` command allows a human to take direct control of a session. This sets the browser session state to `takeover` and pauses agent-led execution, ensuring that the human can resolve complex issues or navigate through manual verification steps before `releasing` the session back to the agent.

## Storage & Artifacts

- **Session Data**: `.niyam/workspace/browser/TASK-ID.json`
- **Action Logs**: `.niyam/workspace/browser/TASK-ID-actions.jsonl`
- **Screenshots**: `.niyam/workspace/artifacts/TASK-ID/screenshots/`
