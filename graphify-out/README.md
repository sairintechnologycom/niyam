# Graphify Reference

This directory stores generated Graphify artifacts for future codebase reference.

## Files

- `graph.json`: Graphify code graph.
- `GRAPH_TREE.html`: Browsable D3 tree generated from `graph.json`.
- `sutra-callflow.html`: Mermaid call-flow HTML generated from `graph.json`.

## Generation Notes

Graphify was installed as:

```bash
uv tool install graphifyy
```

The full repository contains many Markdown/docs/image files. Current Graphify extraction requires an LLM API key for semantic extraction of those files. To avoid depending on external keys, this graph was generated from a temporary Python-only mirror of:

- `niyam/`
- `tests/`

The temporary mirror excluded Markdown, images, Jinja templates, YAML rule files, lockfiles, environment fixtures, and other non-Python files.

Commands used:

```bash
graphify extract /tmp/sutra-graph-code --no-cluster --out .
graphify tree --graph graphify-out/graph.json --output graphify-out/GRAPH_TREE.html --root /tmp/sutra-graph-code --label sutra-niyam-code
graphify export callflow-html
```

Result:

- `graph.json`: `3133` nodes, `8704` edges.
- `GRAPH_TREE.html`: generated successfully.
- `sutra-callflow.html`: generated successfully.

Known limitation:

- `graphify benchmark graphify-out/graph.json` failed with `KeyError: 'links'` because the generated Graphify JSON uses an `edges` key. The graph itself loaded for tree and call-flow generation.

Human-readable companion docs:

- `docs/codebase/feature-catalog.md`
- `docs/codebase/code-structure.md`

