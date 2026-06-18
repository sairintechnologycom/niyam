from __future__ import annotations

import difflib
from typing import List

from niyam.suggestions.registry import CommandRegistry
from niyam.suggestions.aliases import get_aliases, resolve_alias


class SuggestionEngine:
    def __init__(self, registry: CommandRegistry):
        self.registry = registry

    def suggest(self, partial_command: str) -> List[str]:
        # Resolve aliases on the first token if possible
        resolved_command = resolve_alias(partial_command)
        
        # We need to preserve trailing space if user typed "loop "
        has_trailing_space = partial_command.endswith(" ")
        tokens = resolved_command.split()
        
        if not tokens:
            # If empty, suggest top level commands
            return list(self.registry.root.subcommands.keys())
            
        if has_trailing_space:
            tokens.append("")
            
        return self._suggest_for_tokens(tokens)

    def _suggest_for_tokens(self, tokens: List[str]) -> List[str]:
        current = self.registry.root
        path = []
        
        for i, token in enumerate(tokens[:-1]):
            # Try to navigate down the tree
            if token in current.subcommands:
                current = current.subcommands[token]
                path.append(token)
            else:
                # We got stuck before the last token.
                # Check if it's an argument or flag for the current node.
                # If we are at a leaf or intermediate node and hit something unknown,
                # we just stay at the current node but we can't traverse further in subcommands.
                # Actually, if we're evaluating something like `loop run --planner claude `,
                # `tokens` will be `["loop", "run", "--planner", "claude", ""]`.
                # We'll reach `run` node.
                pass
                
        # Now we are at `current` node, evaluating `tokens[-1]`
        last_token = tokens[-1]
        
        # Check if the previous token was a flag that expects a value
        if len(tokens) >= 2:
            prev_token = tokens[-2]
            if prev_token in current.flags and prev_token in current.value_providers:
                provider = current.value_providers[prev_token]
                values = provider()
                return self._filter_and_rank(last_token, values)

        # If last token starts with '-', suggest flags
        if last_token.startswith("-"):
            return self._filter_and_rank(last_token, current.flags)

        # If not a flag, it could be a subcommand, an alias, or a positional argument.
        suggestions = []
        
        # Add subcommands
        for sub_name in current.subcommands.keys():
            suggestions.append(sub_name)

        # If there's an __args__ provider, add those
        if "__args__" in current.value_providers:
            suggestions.extend(current.value_providers["__args__"]())
            
        # Add aliases if we are at root
        if current == self.registry.root:
            suggestions.extend(get_aliases().keys())

        # Typo correction and ranking
        return self._filter_and_rank(last_token, suggestions)

    def _filter_and_rank(self, prefix: str, candidates: List[str]) -> List[str]:
        if not prefix:
            return sorted(list(set(candidates)))

        # 1. Exact prefix match
        exact_prefix = [c for c in candidates if c.startswith(prefix)]
        
        # 2. Fuzzy match (Typo correction)
        fuzzy = difflib.get_close_matches(prefix, candidates, n=5, cutoff=0.6)
        
        # Combine and deduplicate, keeping order
        result = []
        seen = set()
        for c in exact_prefix + fuzzy:
            if c not in seen:
                result.append(c)
                seen.add(c)
                
        return result
