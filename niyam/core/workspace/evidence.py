"""Workspace evidence generation."""

from datetime import datetime, timezone
from typing import Dict, Any

from .store import WorkspaceStore
from .timeline import WorkspaceTimeline
from .approvals import WorkspaceApprovals
from .browser import BrowserStore


class WorkspaceEvidence:
    def __init__(
        self,
        store: WorkspaceStore,
        timeline: WorkspaceTimeline,
        approvals: WorkspaceApprovals,
        browser_store: BrowserStore = None,
    ):
        self.store = store
        self.timeline = timeline
        self.approvals = approvals
        self.browser_store = browser_store

    def generate_json(self, session_id: str) -> Dict[str, Any]:
        session = self.store.get_session(session_id)
        if not session:
            return {}

        actions = self.timeline.get_actions(session_id)
        approvals = self.approvals.get_approvals(session_id)

        # Count actions by type
        action_counts = {}
        for action in actions:
            action_counts[action.action_type] = (
                action_counts.get(action.action_type, 0) + 1
            )

        pending_approvals = [a for a in approvals if a.status == "pending"]
        approved_approvals = [a for a in approvals if a.status == "approved"]
        rejected_approvals = [a for a in approvals if a.status == "rejected"]

        recent_actions = [
            a.model_dump(mode="json")
            for a in sorted(actions, key=lambda x: x.timestamp, reverse=True)[:10]
        ]

        redacted = any(a.redacted for a in actions)

        # Include browser data if available
        browser_data = None
        if self.browser_store:
            b_session = self.browser_store.get_session(session_id)
            if b_session:
                b_actions = self.browser_store.get_actions(session_id)
                b_action_counts = {}
                for ba in b_actions:
                    b_action_counts[ba.action_type] = (
                        b_action_counts.get(ba.action_type, 0) + 1
                    )

                screenshots = [
                    ba.output
                    for ba in b_actions
                    if ba.action_type == "screenshot" and ba.output
                ]

                browser_data = {
                    "status": b_session.status,
                    "takeover_by": b_session.takeover_by,
                    "action_counts": b_action_counts,
                    "screenshots": screenshots,
                    "approval_required_actions": len(
                        [ba for ba in b_actions if ba.status == "approval_required"]
                    ),
                }

        return {
            "session": session.model_dump(mode="json"),
            "status": session.status,
            "risk_level": session.risk,
            "action_counts": action_counts,
            "approvals": {
                "pending": len(pending_approvals),
                "approved": len(approved_approvals),
                "rejected": len(rejected_approvals),
                "details": [a.model_dump(mode="json") for a in approvals],
            },
            "memory_refs": session.memory_refs,
            "browser": browser_data,
            "recent_actions": recent_actions,
            "redacted": redacted,
            "exported_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_markdown(self, session_id: str) -> str:
        data = self.generate_json(session_id)
        if not data:
            return f"Session {session_id} not found."

        session = data["session"]
        lines = [
            f"# Workspace Session: {session['id']}",
            f"**Title**: {session['title']}",
            f"**Status**: {data['status']}",
            f"**Risk Level**: {data['risk_level']}",
            f"**Exported At**: {data['exported_at']}",
            ""
        ]

        if data["redacted"]:
            lines.extend([
                "### :warning: Security Notice",
                "This timeline contains redacted sensitive information.",
                ""
            ])

        lines.extend([
            "## Action Summary"
        ])
        for a_type, count in data["action_counts"].items():
            lines.append(f"- **{a_type}**: {count}")
        lines.append("")

        lines.extend([
            "## Approvals",
            f"- **Pending**: {data['approvals']['pending']}",
            f"- **Approved**: {data['approvals']['approved']}",
            f"- **Rejected**: {data['approvals']['rejected']}",
            ""
        ])

        if data.get("browser"):
            b_data = data["browser"]
            lines.extend([
                "## Browser Session",
                f"- **Status**: {b_data['status']}",
            ])
            if b_data.get("takeover_by"):
                lines.append(f"- **Takeover By**: {b_data['takeover_by']}")

            lines.append("- **Action Counts**:")
            for bt, bc in b_data["action_counts"].items():
                lines.append(f"  - **{bt}**: {bc}")
            lines.append(
                f"- **Approval Required Actions**: "
                f"{b_data['approval_required_actions']}"
            )
            lines.append(f"- **Screenshots**: {len(b_data['screenshots'])}")
            lines.append("")

        if session["memory_refs"]:
            lines.extend([
                "## Memory References",
                ", ".join(session["memory_refs"]),
                ""
            ])

        lines.extend([
            "## Recent Actions"
        ])
        for action in data["recent_actions"]:
            lines.append(
                f"- [{action['timestamp']}] **{action['action_type']}** "
                f"by {action['actor']} (Risk: {action['risk']})"
            )

        return "\n".join(lines)
