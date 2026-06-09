"""Workspace evidence generation."""

import json
from datetime import datetime
from typing import Dict, Any

from .models import WorkspaceSession
from .store import WorkspaceStore
from .timeline import WorkspaceTimeline
from .approvals import WorkspaceApprovals


class WorkspaceEvidence:
    def __init__(self, store: WorkspaceStore, timeline: WorkspaceTimeline, approvals: WorkspaceApprovals):
        self.store = store
        self.timeline = timeline
        self.approvals = approvals

    def generate_json(self, session_id: str) -> Dict[str, Any]:
        session = self.store.get_session(session_id)
        if not session:
            return {}

        actions = self.timeline.get_actions(session_id)
        approvals = self.approvals.get_approvals(session_id)

        # Count actions by type
        action_counts = {}
        for action in actions:
            action_counts[action.action_type] = action_counts.get(action.action_type, 0) + 1

        pending_approvals = [a for a in approvals if a.status == "pending"]
        approved_approvals = [a for a in approvals if a.status == "approved"]
        rejected_approvals = [a for a in approvals if a.status == "rejected"]

        recent_actions = [a.model_dump() for a in sorted(actions, key=lambda x: x.timestamp, reverse=True)[:10]]

        redacted = any(a.redacted for a in actions)

        return {
            "session": session.model_dump(),
            "status": session.status,
            "risk_level": session.risk,
            "action_counts": action_counts,
            "approvals": {
                "pending": len(pending_approvals),
                "approved": len(approved_approvals),
                "rejected": len(rejected_approvals),
                "details": [a.model_dump() for a in approvals]
            },
            "memory_refs": session.memory_refs,
            "recent_actions": recent_actions,
            "redacted": redacted,
            "exported_at": datetime.utcnow().isoformat(),
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
            lines.append(f"- [{action['timestamp']}] **{action['action_type']}** by {action['actor']} (Risk: {action['risk']})")

        return "\n".join(lines)
