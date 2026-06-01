# Migration Guide: Upgrading from Sutra to Niyam

This guide describes how to upgrade your existing workspaces, CLI, configuration, and workflows from the legacy **Sutra** codename to the new **Niyam** product identity.

## Why the Rename Happened

The product has officially transitioned from its codename **Sutra** to its production brand name **Niyam**. Along with this rebranding, the CLI command, config structures, and libraries are renamed for a unified brand identity:
- **Product Name**: Niyam (meaning "governed rule" or "order")
- **CLI Command**: `niyam`
- **Configuration Directory**: `.niyam/`
- **Main Config File**: `niyam.yaml`
- **PyPI Package**: `niyam-dev`

---

## Command Mapping

All CLI commands have been renamed from `sutra` to `niyam`. Below is a mapping of the most common commands:

| Legacy Command | New Command | Description |
|---|---|---|
| `sutra init` | `niyam init` | Initialize a governed Niyam workspace |
| `sutra doctor` | `niyam doctor` | Validate workspace integrity |
| `sutra sync` | `niyam sync` | Synchronize .niyam/ to runtimes |
| `sutra run` | `niyam run` | Run a single-agent mission |
| `sutra mission start` | `niyam mission start` | Start execution of a mission |
| `sutra setup` | `niyam setup` | Run onboarding wizard |

---

## Workspace Migration (.sutra/ to .niyam/)

Niyam includes built-in migration utility to migrate legacy Sutra workspaces safely.

### The Recommended Migration Command

To migrate an existing repository automatically, run:

```bash
niyam migrate --from-sutra
```

### How It Works Safely

1. **Safe Copy (Default)**: The command copies `.sutra/` contents to `.niyam/` by default. It does not delete your original `.sutra/` folder unless you specify the `--move` flag.
2. **Config File Rename**: It renames `.sutra/sutra.yaml` to `.niyam/niyam.yaml`.
3. **Internal Reference Updates**: It automatically updates internal file contents and references inside `.niyam/` (such as in agents, skills, and policies markdown/YAML files) from `sutra` to `niyam`.
4. **Safety Check**: If `.niyam/` already exists, the command will abort unless you pass the `--force` flag.

### Post-Migration Steps

After running `niyam migrate --from-sutra`, you should:
1. Verify the `.niyam/` folder has been generated correctly.
2. Verify you can run `niyam doctor` without errors.
3. Remove the legacy `.sutra/` directory manually:
   ```bash
   rm -rf .sutra/
   ```

---

## Compatibility and Deprecation Behavior

To prevent breaking existing workflows, Niyam maintains backward-compatible fallback logic for a short deprecation window:
1. **Fallback Configuration Folder**: If `.sutra/` exists in a repository but `.niyam/` does not, Niyam will read the configuration from `.sutra/` and output a warning requesting you to migrate.
2. **Fallback Configuration File**: If `sutra.yaml` exists instead of `niyam.yaml` in the configuration folder, Niyam will parse it as a fallback.
3. **Deprecated CLI command**: Running the legacy `sutra` command will print a deprecation warning and point you to the new `niyam` commands:
   ```text
   Sutra has been renamed to Niyam.

   Use:
     niyam <command>

   Migration:
     niyam migrate --from-sutra

   The deprecated `sutra` command will be removed in a future release.
   ```
