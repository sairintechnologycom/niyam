from __future__ import annotations

from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field

from niyam.suggestions.providers import get_runtimes, get_loop_specs, get_recent_loop_runs

@dataclass
class CommandNode:
    name: str
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)
    category: str = "general"
    # Mapping of flag/argument name to a value provider function. 
    # The special key "__args__" maps to a provider for positional arguments.
    value_providers: Dict[str, Callable[[], List[str]]] = field(default_factory=dict)
    subcommands: Dict[str, "CommandNode"] = field(default_factory=dict)

    def add_subcommand(self, node: "CommandNode") -> None:
        self.subcommands[node.name] = node


class CommandRegistry:
    def __init__(self):
        self.root = CommandNode(name="niyam")

    def register(self, path: List[str], node: CommandNode) -> None:
        if not path:
            return
        
        current = self.root
        for p in path[:-1]:
            if p not in current.subcommands:
                current.add_subcommand(CommandNode(name=p))
            current = current.subcommands[p]
        current.add_subcommand(node)

    def get_node(self, path: List[str]) -> Optional[CommandNode]:
        current = self.root
        for p in path:
            if p in current.subcommands:
                current = current.subcommands[p]
            else:
                return None
        return current


def build_default_registry() -> CommandRegistry:
    registry = CommandRegistry()

    # Evidence commands
    registry.register(["evidence"], CommandNode(
        name="evidence",
        description="Audit-ready evidence and readiness report generation.",
        subcommands={}
    ))
    registry.register(["evidence", "verify"], CommandNode(
        name="verify",
        description="Verify evidence.",
        flags=["--bundle", "--output"],
    ))

    # Loop commands
    registry.register(["loop"], CommandNode(
        name="loop",
        description="Governed AI agent feedback loops (LoopOps).",
        subcommands={}
    ))
    
    registry.register(["loop", "init"], CommandNode(
        name="init",
        description="Generate a starter LoopSpec YAML file.",
        flags=["--name", "--type", "-n", "-t"],
    ))
    
    registry.register(["loop", "validate"], CommandNode(
        name="validate",
        description="Validate a LoopSpec YAML file against schema and semantic rules.",
        value_providers={"__args__": get_loop_specs},
    ))
    
    registry.register(["loop", "run"], CommandNode(
        name="run",
        description="Run a loop specification governed by Niyam LoopOps.",
        flags=[
            "--scenario", "-s", "--planner", "--implementer", "--reviewer",
            "--dry-run", "--mode", "--require-approval-on", "--max-iterations",
            "--max-cost-usd", "--replay", "--fleet"
        ],
        value_providers={
            "__args__": get_loop_specs,
            "--planner": get_runtimes,
            "--implementer": get_runtimes,
            "--reviewer": get_runtimes,
            "--replay": get_recent_loop_runs,
        }
    ))
    
    registry.register(["loop", "review"], CommandNode(
        name="review",
        description="Review a diff using a chosen reviewer and policy rules.",
        flags=["--diff", "--reviewer", "--policy"],
        value_providers={
            "--reviewer": get_runtimes,
        }
    ))
    
    registry.register(["loop", "report"], CommandNode(
        name="report",
        description="Generate or retrieve a report for a specific LoopRun from evidence.",
        flags=["--format", "-f", "--output", "-o"],
        value_providers={
            "__args__": get_recent_loop_runs,
        }
    ))
    
    registry.register(["loop", "evidence"], CommandNode(
        name="evidence",
        description="Package the evidence directory of a LoopRun into a zip archive.",
        flags=["--bundle", "-b"],
        value_providers={
            "__args__": get_recent_loop_runs,
        }
    ))

    # Completion commands
    registry.register(["completion"], CommandNode(
        name="completion",
        description="Shell completion tools.",
        subcommands={}
    ))
    registry.register(["completion", "script"], CommandNode(
        name="script",
        description="Print completion script for a given shell.",
        flags=["--shell"],
        value_providers={"--shell": lambda: ["bash", "zsh", "fish", "powershell"]}
    ))
    registry.register(["completion", "install"], CommandNode(
        name="install",
        description="Install completion script for a given shell.",
        flags=["--shell"],
        value_providers={"--shell": lambda: ["bash", "zsh", "fish", "powershell"]}
    ))

    # Suggest command
    registry.register(["suggest"], CommandNode(
        name="suggest",
        description="Suggest completions based on partial input.",
    ))
    
    # Let's add other top-level commands as empty nodes for completion
    for cmd in ["context", "guard", "mcp", "rules", "skills", "policy", "cost", "runtime", "pack", "memory", "mission", "review", "pr", "ci", "identity", "saas", "fleet", "swarm", "workspace"]:
        registry.register([cmd], CommandNode(name=cmd))

    return registry

registry = build_default_registry()
