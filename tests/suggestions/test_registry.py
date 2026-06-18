from niyam.suggestions.registry import CommandRegistry, CommandNode, build_default_registry

def test_registry_registration():
    registry = CommandRegistry()
    node = CommandNode(name="run", description="Run loop")
    registry.register(["loop", "run"], node)

    assert registry.get_node(["loop"]) is not None
    assert registry.get_node(["loop"]).name == "loop"
    
    run_node = registry.get_node(["loop", "run"])
    assert run_node is not None
    assert run_node.name == "run"
    assert run_node.description == "Run loop"

def test_build_default_registry():
    registry = build_default_registry()
    loop_node = registry.get_node(["loop"])
    assert loop_node is not None
    
    run_node = registry.get_node(["loop", "run"])
    assert run_node is not None
    assert "--planner" in run_node.flags
    assert "--planner" in run_node.value_providers
