
## Validation Run - 2026-05-30T06:22:51.970812Z
**Command:** `ruff format --check .`
**Exit Code:** `1`

### stdout
```
Would reformat: niyam/cli.py
Would reformat: niyam/core/ci.py
Would reformat: niyam/core/config.py
Would reformat: niyam/core/context.py
Would reformat: niyam/core/doctor.py
Would reformat: niyam/core/init.py
Would reformat: niyam/core/memory.py
Would reformat: niyam/core/packs.py
Would reformat: niyam/core/pr.py
Would reformat: niyam/core/review.py
Would reformat: niyam/core/security.py
Would reformat: niyam/core/setup.py
Would reformat: niyam/core/sync.py
Would reformat: niyam/evidence/reporter.py
Would reformat: niyam/mission/dashboard.py
Would reformat: niyam/mission/executor.py
Would reformat: niyam/mission/planner.py
Would reformat: niyam/mission/reporter.py
Would reformat: niyam/mission/status.py
Would reformat: niyam/mission/validator.py
Would reformat: niyam/policies/guard.py
Would reformat: niyam/policies/validator.py
Would reformat: niyam/runtimes/claude.py
Would reformat: niyam/runtimes/codex.py
Would reformat: niyam/runtimes/gemini.py
Would reformat: tests/conftest.py
Would reformat: tests/test_ci.py
Would reformat: tests/test_dashboard.py
Would reformat: tests/test_doctor_enhanced.py
Would reformat: tests/test_fleet.py
Would reformat: tests/test_guardrails.py
Would reformat: tests/test_hooks.py
Would reformat: tests/test_init.py
Would reformat: tests/test_memory.py
Would reformat: tests/test_mission.py
Would reformat: tests/test_multi_runtime.py
Would reformat: tests/test_packs.py
Would reformat: tests/test_pr.py
Would reformat: tests/test_recovery.py
Would reformat: tests/test_remediation.py
Would reformat: tests/test_review.py
Would reformat: tests/test_run_composite.py
Would reformat: tests/test_setup.py
Would reformat: tests/test_sync.py
Would reformat: tests/test_templates.py
Would reformat: tests/test_verification.py
46 files would be reformatted, 13 files already formatted

```

## Validation Run - 2026-05-30T06:22:52.008076Z
**Command:** `ruff check .`
**Exit Code:** `1`

### stdout
```
F401 [*] `pathlib.Path` imported but unused
 --> niyam/cli.py:6:21
  |
5 | from enum import Enum
6 | from pathlib import Path
  |                     ^^^^
7 | from typing import Annotated, Optional
  |
help: Remove unused import: `pathlib.Path`

F541 [*] f-string without any placeholders
   --> niyam/cli.py:210:19
    |
209 |     # 3. Plan the mission
210 |     console.print(f"\n[cyan]3. Generating mission plan...[/]")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
211 |     mission_id = run_mission_plan(
212 |         requirements_path=requirement,
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/cli.py:220:19
    |
219 |     # 4. Approve plan
220 |     console.print(f"\n[cyan]4. Checking plan approval...[/]")
    |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
221 |     run_mission_approve(console=console, interactive=not auto_approve)
    |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> niyam/core/ci.py:6:8
  |
5 | import json
6 | import os
  |        ^^
7 | import fnmatch
8 | import subprocess
  |
help: Remove unused import: `os`

F401 [*] `pathlib.Path` imported but unused
  --> niyam/core/ci.py:10:21
   |
 8 | import subprocess
 9 | from datetime import datetime, timezone
10 | from pathlib import Path
   |                     ^^^^
11 |
12 | import yaml
   |
help: Remove unused import: `pathlib.Path`

F401 [*] `yaml` imported but unused
  --> niyam/core/ci.py:12:8
   |
10 | from pathlib import Path
11 |
12 | import yaml
   |        ^^^^
13 | from rich.console import Console
14 | from rich.panel import Panel
   |
help: Remove unused import: `yaml`

F401 [*] `rich.table.Table` imported but unused
  --> niyam/core/ci.py:15:24
   |
13 | from rich.console import Console
14 | from rich.panel import Panel
15 | from rich.table import Table
   |                        ^^^^^
16 |
17 | from niyam.core.config import (
   |
help: Remove unused import: `rich.table.Table`

F401 [*] `niyam.core.config.load_niyam_config` imported but unused
  --> niyam/core/ci.py:21:5
   |
19 |     get_niyam_dir,
20 |     load_project_config,
21 |     load_niyam_config,
   |     ^^^^^^^^^^^^^^^^^
22 | )
23 | from niyam.mission.planner import get_latest_mission_id
   |
help: Remove unused import: `niyam.core.config.load_niyam_config`

F401 [*] `niyam.mission.reporter.compute_sha256` imported but unused
  --> niyam/core/ci.py:24:55
   |
22 | )
23 | from niyam.mission.planner import get_latest_mission_id
24 | from niyam.mission.reporter import run_verify_report, compute_sha256
   |                                                       ^^^^^^^^^^^^^^
25 | from niyam.policies.guard import load_security_policy
   |
help: Remove unused import: `niyam.mission.reporter.compute_sha256`

F541 [*] f-string without any placeholders
  --> niyam/core/ci.py:48:19
   |
46 |     failures = []
47 |
48 |     console.print(f"[cyan]Niyam CI/CD Verification[/]")
   |                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
49 |     console.print(f"Target Branch: [bold cyan]{target_branch}[/]")
50 |     console.print(f"Strict Mode: [bold]{'Enabled' if strict else 'Disabled'}[/]")
   |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
  --> niyam/core/ci.py:69:33
   |
67 |         except SystemExit as e:
68 |             if e.code != 0:
69 |                 failures.append(f"Evidence integrity check failed.")
   |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
70 |                 integrity_status = "failed"
71 |             else:
   |
help: Remove extraneous `f` prefix

E402 Module level import not at top of file
   --> niyam/core/config.py:143:1
    |
143 | from pydantic import BaseModel, Field, AliasChoices
    | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
144 |
145 | class TaskValidationConfig(BaseModel):
    |

F541 [*] f-string without any placeholders
   --> niyam/core/context.py:411:26
    |
409 |         for cmd_type, cmd in scan_result["validation"].items():
410 |             lines.append(f"## {cmd_type.title()}")
411 |             lines.append(f"```bash")
    |                          ^^^^^^^^^^
412 |             lines.append(f"{cmd}")
413 |             lines.append(f"```")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/core/context.py:413:26
    |
411 |             lines.append(f"```bash")
412 |             lines.append(f"{cmd}")
413 |             lines.append(f"```")
    |                          ^^^^^^
414 |             lines.append("")
415 |     else:
    |
help: Remove extraneous `f` prefix

F401 [*] `rich.panel.Panel` imported but unused
  --> niyam/core/doctor.py:9:24
   |
 7 | import yaml
 8 | from rich.console import Console
 9 | from rich.panel import Panel
   |                        ^^^^^
10 | from rich.table import Table
   |
help: Remove unused import: `rich.panel.Panel`

F821 Undefined name `NiyamConfig`
   --> niyam/core/doctor.py:236:54
    |
236 | def _check_runtimes_in_path(repo_root: Path, config: NiyamConfig) -> list[DiagnosticResult]:
    |                                                      ^^^^^^^^^^^
237 |     import shutil
238 |     results = []
    |

F401 [*] `niyam.core.config.NiyamConfig` imported but unused
   --> niyam/core/doctor.py:335:35
    |
334 |     # core load config
335 |     from niyam.core.config import NiyamConfig
    |                                   ^^^^^^^^^^^
336 |     config = load_niyam_config(root)
    |
help: Remove unused import: `niyam.core.config.NiyamConfig`

F401 [*] `shutil` imported but unused
 --> niyam/core/packs.py:5:8
  |
3 | from __future__ import annotations
4 |
5 | import shutil
  |        ^^^^^^
6 | from pathlib import Path
7 | import yaml
  |
help: Remove unused import: `shutil`

F401 [*] `niyam.core.config.NIYAM_DIR` imported but unused
  --> niyam/core/packs.py:11:5
   |
10 | from niyam.core.config import (
11 |     NIYAM_DIR,
   |     ^^^^^^^^^
12 |     get_niyam_dir,
13 |     load_niyam_config,
   |
help: Remove unused import: `niyam.core.config.NIYAM_DIR`

F841 Local variable `manifest` is assigned to but never used
  --> niyam/core/packs.py:67:5
   |
65 |     """Install a pack into the .niyam/ directory."""
66 |     pack_dir = get_pack_dir(name)
67 |     manifest = load_pack_manifest(name)
   |     ^^^^^^^^
68 |     niyam_dir = get_niyam_dir(repo_root)
   |
help: Remove assignment to unused variable `manifest`

F541 [*] f-string without any placeholders
   --> niyam/core/packs.py:105:17
    |
103 |         if conflicts:
104 |             raise ValueError(
105 |                 f"Conflict detected! The following files already exist in .niyam/:\n"
    |                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
106 |                 + "\n".join(f"  - {c}" for c in conflicts)
107 |                 + "\nUse --force to overwrite them."
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/core/pr.py:311:18
    |
309 |     if is_test:
310 |         console.print("[dim]Mocking PR creation...[/]")
311 |         pr_url = f"https://github.com/mock/repo/pull/42"
    |                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
312 |     else:
313 |         token = token or os.environ.get("GITHUB_TOKEN")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/core/review.py:153:23
    |
151 |     if is_test:
152 |         console.print("[dim]Mocking review execution...[/]")
153 |         console.print(f"[green]✓[/] Code review successfully generated.")
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
154 |     else:
155 |         if shutil.which(runtime):
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/core/review.py:161:31
    |
159 |             except Exception:
160 |                 console.print(f"[yellow]Warning: {runtime} execution failed.[/]")
161 |                 console.print(f"Here is the review prompt. You can copy-paste it into your AI session:\n")
    |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
162 |                 console.print(compiled_prompt)
163 |         else:
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/core/review.py:165:27
    |
163 |         else:
164 |             console.print(f"[yellow]CLI '{runtime}' not found in PATH.[/]")
165 |             console.print(f"Here is the generated review prompt. You can copy-paste it into your session:\n")
    |                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
166 |             console.print(compiled_prompt)
167 |             console.print(f"\n[dim]Prompt also saved to: {prompt_file}[/]")
    |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> niyam/core/setup.py:5:8
  |
3 | from __future__ import annotations
4 |
5 | import os
  |        ^^
6 | import shutil
7 | from pathlib import Path
  |
help: Remove unused import: `os`

F401 [*] `rich.panel.Panel` imported but unused
  --> niyam/core/sync.py:9:24
   |
 7 | import yaml
 8 | from rich.console import Console
 9 | from rich.panel import Panel
   |                        ^^^^^
10 |
11 | from niyam.core.config import (
   |
help: Remove unused import: `rich.panel.Panel`

F541 [*] f-string without any placeholders
   --> niyam/evidence/reporter.py:159:9
    |
157 |         f"**Branch:** `{branch}`",
158 |         f"**Generated:** {now}",
159 |         f"**Generator:** Niyam v0.1.0",
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
160 |         "",
161 |         "---",
    |
help: Remove extraneous `f` prefix

F401 [*] `os` imported but unused
 --> niyam/mission/dashboard.py:6:8
  |
5 | import json
6 | import os
  |        ^^
7 | import time
8 | from pathlib import Path
  |
help: Remove unused import: `os`

F541 [*] f-string without any placeholders
   --> niyam/mission/executor.py:763:35
    |
761 |                 with _print_lock:
762 |                     console.print(f"[yellow]Orchestrator '{orchestrator}' CLI not found in PATH.[/]")
763 |                     console.print(f"Please run the task using the prompt at:")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
764 |                     console.print(f"  [bold]cat {prompt_path}[/]")
765 |                     console.print("\nPress Enter once you have executed the prompt and completed the work...")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/mission/executor.py:903:33
    |
901 |                     with open(val_path, mode, encoding="utf-8") as f:
902 |                         f.write(f"\n## Validation Check - {name} - {timestamp}\n")
903 |                         f.write(f"**Status:** ℹ SKIPPED — Not configured\n\n")
    |                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
904 |
905 |         # Run task-specific checks
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
    --> niyam/mission/executor.py:1202:80
     |
1200 |                             t["status"] = "skipped"
1201 |                             save_plan(run_dir, plan_data)
1202 |                             log_execution_event(run_dir, "TASK_SKIPPED", t_id, f"Dependency failed, skipping task.")
     |                                                                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1203 |                             continue
1204 |                         ready_tasks.append(t)
     |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
    --> niyam/mission/executor.py:1262:75
     |
1260 |                         failed_tasks.add(t_id)
1261 |                         save_plan(run_dir, plan_data)
1262 |                         log_execution_event(run_dir, "TASK_FAILED", t_id, f"Task execution failed.")
     |                                                                           ^^^^^^^^^^^^^^^^^^^^^^^^^
1263 |                         with _print_lock:
1264 |                             console.print(f"[bold red]❌[/] Task {t_id} failed.\n")
     |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/mission/planner.py:637:23
    |
635 |         validate_mission_plan(plan_path, repo_root)
636 |     except PlanValidationError as e:
637 |         console.print(f"[bold red]❌ Mission approval rejected due to validation failures:[/]")
    |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
638 |         for err in e.errors:
639 |             console.print(f"  • [red]{err}[/]")
    |
help: Remove extraneous `f` prefix

F541 [*] f-string without any placeholders
   --> niyam/mission/planner.py:714:35
    |
712 |                     console.print("[bold green]✓ Edited plan is valid.[/]")
713 |                 except PlanValidationError as e:
714 |                     console.print(f"[bold red]❌ Mission plan validation failed after editing:[/]")
    |                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
715 |                     for err in e.errors:
716 |                         console.print(f"  • [red]{err}[/]")
    |
help: Remove extraneous `f` prefix

F401 [*] `yaml` imported but unused
  --> niyam/mission/reporter.py:9:8
   |
 7 | import subprocess
 8 | from datetime import datetime
 9 | import yaml
   |        ^^^^
10 | from rich.console import Console
11 | from rich.panel import Panel
   |
help: Remove unused import: `yaml`

F401 [*] `pathlib.Path` imported but unused
 --> niyam/mission/status.py:5:21
  |
3 | from __future__ import annotations
4 |
5 | from pathlib import Path
  |                     ^^^^
6 | from rich.console import Console
7 | from rich.table import Table
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `os` imported but unused
 --> niyam/mission/validator.py:5:8
  |
3 | from __future__ import annotations
4 |
5 | import os
  |        ^^
6 | import shutil
7 | from pathlib import Path
  |
help: Remove unused import: `os`

F401 [*] `yaml` imported but unused
 --> niyam/mission/validator.py:8:8
  |
6 | import shutil
7 | from pathlib import Path
8 | import yaml
  |        ^^^^
9 | from pydantic import ValidationError
  |
help: Remove unused import: `yaml`

E741 Ambiguous variable name: `l`
  --> niyam/mission/validator.py:43:46
   |
41 |     except ValidationError as e:
42 |         for err in e.errors():
43 |             loc_str = " -> ".join(str(l) for l in err["loc"])
   |                                              ^
44 |             errors.append(f"Schema violation at {loc_str}: {err['msg']}")
45 |         raise PlanValidationError(errors)
   |

F401 [*] `pathlib.Path` imported but unused
 --> niyam/policies/validator.py:5:21
  |
3 | from __future__ import annotations
4 |
5 | from pathlib import Path
  |                     ^^^^
6 |
7 | import yaml
  |
help: Remove unused import: `pathlib.Path`

F401 [*] `yaml` imported but unused
 --> niyam/policies/validator.py:7:8
  |
5 | from pathlib import Path
6 |
7 | import yaml
  |        ^^^^
8 | from rich.console import Console
9 | from rich.table import Table
  |
help: Remove unused import: `yaml`

F541 [*] f-string without any placeholders
  --> niyam/runtimes/claude.py:30:23
   |
28 |         self._generate_hooks(console)
29 |         self._generate_settings(console)
30 |         console.print(f"[green]✓[/] Claude Code runtime synced")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
31 |
32 |     def clean(self, console: Console) -> None:
   |
help: Remove extraneous `f` prefix

F401 [*] `shutil` imported but unused
 --> niyam/runtimes/codex.py:5:8
  |
3 | from __future__ import annotations
4 |
5 | import shutil
  |        ^^^^^^
6 | from pathlib import Path
  |
help: Remove unused import: `shutil`

F401 [*] `pathlib.Path` imported but unused
 --> niyam/runtimes/codex.py:6:21
  |
5 | import shutil
6 | from pathlib import Path
  |                     ^^^^
7 |
8 | import yaml
  |
help: Remove unused import: `pathlib.Path`

F541 [*] f-string without any placeholders
  --> niyam/runtimes/codex.py:24:23
   |
22 |         """Generate Codex CLI files from .niyam/ source of truth."""
23 |         self._generate_agents_md(console)
24 |         console.print(f"[green]✓[/] Codex CLI runtime synced")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
25 |
26 |     def clean(self, console: Console) -> None:
   |
help: Remove extraneous `f` prefix

F401 [*] `pathlib.Path` imported but unused
 --> niyam/runtimes/gemini.py:7:21
  |
5 | import json
6 | import shutil
7 | from pathlib import Path
  |                     ^^^^
8 |
9 | import yaml
  |
help: Remove unused import: `pathlib.Path`

F541 [*] f-string without any placeholders
  --> niyam/runtimes/gemini.py:27:23
   |
25 |         self._generate_style_md(console)
26 |         self._generate_settings(console)
27 |         console.print(f"[green]✓[/] Gemini CLI runtime synced")
   |                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
28 |
29 |     def clean(self, console: Console) -> None:
   |
help: Remove extraneous `f` prefix

F401 [*] `niyam.mission.executor.run_mission_resume` imported but unused
  --> tests/test_ci.py:13:55
   |
11 | from niyam.core.config import get_niyam_dir
12 | from niyam.mission.planner import run_mission_plan
13 | from niyam.mission.executor import run_mission_start, run_mission_resume, load_plan
   |                                                       ^^^^^^^^^^^^^^^^^^
   |
help: Remove unused import: `niyam.mission.executor.run_mission_resume`

F401 [*] `urllib.request` imported but unused
  --> tests/test_ci.py:83:12
   |
82 |     from unittest.mock import patch, MagicMock
83 |     import urllib.request
   |            ^^^^^^^^^^^^^^
84 |     
85 |     mock_response = MagicMock()
   |
help: Remove unused import: `urllib.request`

F401 [*] `urllib.error` imported but unused
   --> tests/test_ci.py:125:12
    |
124 |     from unittest.mock import patch
125 |     import urllib.error
    |            ^^^^^^^^^^^^
126 |
127 |     with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
    |
help: Remove unused import: `urllib.error`

F401 [*] `pytest` imported but unused
  --> tests/test_dashboard.py:8:8
   |
 6 | import os
 7 | from pathlib import Path
 8 | import pytest
   |        ^^^^^^
 9 | from rich.console import Console
10 | from unittest.mock import patch, MagicMock
   |
help: Remove unused import: `pytest`

F401 [*] `unittest.mock.MagicMock` imported but unused
  --> tests/test_dashboard.py:10:34
   |
 8 | import pytest
 9 | from rich.console import Console
10 | from unittest.mock import patch, MagicMock
   |                                  ^^^^^^^^^
11 |
12 | from niyam.core.config import get_niyam_dir
   |
help: Remove unused import: `unittest.mock.MagicMock`

F401 [*] `niyam.mission.executor.load_plan` imported but unused
  --> tests/test_dashboard.py:14:55
   |
12 | from niyam.core.config import get_niyam_dir
13 | from niyam.mission.planner import run_mission_plan, run_mission_approve
14 | from niyam.mission.executor import run_mission_start, load_plan
   |                                                       ^^^^^^^^^
15 | from niyam.mission.dashboard import run_mission_dashboard, generate_dashboard_renderable
   |
help: Remove unused import: `niyam.mission.executor.load_plan`

F841 Local variable `mission_id` is assigned to but never used
  --> tests/test_dashboard.py:72:5
   |
70 |     req_file = niyam_repo / "requirements.md"
71 |     req_file.write_text("# Test Requirements\n", encoding="utf-8")
72 |     mission_id = run_mission_plan(str(req_file), console=console)
   |     ^^^^^^^^^^
73 |     run_mission_approve(console=console)
   |
help: Remove assignment to unused variable `mission_id`

F841 Local variable `mock_update` is assigned to but never used
  --> tests/test_dashboard.py:77:44
   |
75 |     # Mock time.sleep to raise KeyboardInterrupt to exit loop immediately
76 |     with patch("time.sleep", side_effect=KeyboardInterrupt), \
77 |          patch("rich.live.Live.update") as mock_update:
   |                                            ^^^^^^^^^^^
78 |         run_mission_dashboard(watch=True, console=console)
79 |         # Should not raise exception (handled KeyboardInterrupt gracefully)
   |
help: Remove assignment to unused variable `mock_update`

F401 [*] `yaml` imported but unused
  --> tests/test_doctor.py:9:8
   |
 8 | import pytest
 9 | import yaml
   |        ^^^^
10 | from rich.console import Console
   |
help: Remove unused import: `yaml`

F401 [*] `unittest.mock.MagicMock` imported but unused
 --> tests/test_doctor_enhanced.py:7:34
  |
5 | import os
6 | from pathlib import Path
7 | from unittest.mock import patch, MagicMock
  |                                  ^^^^^^^^^
8 | import pytest
9 | from rich.console import Console
  |
help: Remove unused import: `unittest.mock.MagicMock`

F401 [*] `pytest` imported but unused
 --> tests/test_doctor_enhanced.py:8:8
  |
6 | from pathlib import Path
7 | from unittest.mock import patch, MagicMock
8 | import pytest
  |        ^^^^^^
9 | from rich.console import Console
  |
help: Remove unused import: `pytest`

F401 [*] `rich.console.Console` imported but unused
  --> tests/test_doctor_enhanced.py:9:26
   |
 7 | from unittest.mock import patch, MagicMock
 8 | import pytest
 9 | from rich.console import Console
   |                          ^^^^^^^
10 |
11 | from niyam.core.doctor import (
   |
help: Remove unused import: `rich.console.Console`

F401 [*] `niyam.core.doctor.run_doctor` imported but unused
  --> tests/test_doctor_enhanced.py:12:5
   |
11 | from niyam.core.doctor import (
12 |     run_doctor,
   |     ^^^^^^^^^^
13 |     _check_runtimes_in_path,
14 |     _check_agents_validity,
   |
help: Remove unused import: `niyam.core.doctor.run_doctor`

F401 [*] `json` imported but unused
 --> tests/test_fleet.py:6:8
  |
5 | import os
6 | import json
  |        ^^^^
7 | from pathlib import Path
8 | import subprocess
  |
help: Remove unused import: `json`

F401 [*] `yaml` imported but unused
  --> tests/test_fleet.py:10:8
   |
 8 | import subprocess
 9 | import pytest
10 | import yaml
   |        ^^^^
11 | from rich.console import Console
   |
help: Remove unused import: `yaml`

F841 [*] Local variable `e` is assigned to but never used
  --> tests/test_guardrails.py:82:29
   |
80 |                 run_mission_start(console=console, worktree=False)
81 |             assert excinfo.value.code == 1
82 |         except Exception as e:
   |                             ^
83 |             # Let it fail with SystemExit as expected
84 |             pass
   |
help: Remove assignment to unused variable `e`

F401 [*] `unittest.mock.patch` imported but unused
 --> tests/test_hooks.py:7:27
  |
5 | import os
6 | from pathlib import Path
7 | from unittest.mock import patch, MagicMock
  |                           ^^^^^
8 | import pytest
9 | import yaml
  |
help: Remove unused import

F401 [*] `unittest.mock.MagicMock` imported but unused
 --> tests/test_hooks.py:7:34
  |
5 | import os
6 | from pathlib import Path
7 | from unittest.mock import patch, MagicMock
  |                                  ^^^^^^^^^
8 | import pytest
9 | import yaml
  |
help: Remove unused import

F401 [*] `pytest` imported but unused
  --> tests/test_hooks.py:8:8
   |
 6 | from pathlib import Path
 7 | from unittest.mock import patch, MagicMock
 8 | import pytest
   |        ^^^^^^
 9 | import yaml
10 | from rich.console import Console
   |
help: Remove unused import: `pytest`

F401 [*] `pytest` imported but unused
 --> tests/test_memory.py:7:8
  |
5 | import os
6 | from pathlib import Path
7 | import pytest
  |        ^^^^^^
8 | from rich.console import Console
  |
help: Remove unused import: `pytest`

F401 [*] `niyam.mission.planner.get_latest_mission_id` imported but unused
  --> tests/test_mission.py:13:74
   |
12 | from niyam.core.config import get_niyam_dir
13 | from niyam.mission.planner import run_mission_plan, run_mission_approve, get_latest_mission_id
   |                                                                          ^^^^^^^^^^^^^^^^^^^^^
14 | from niyam.mission.executor import run_mission_start, run_mission_pause, run_mission_resume, load_plan
15 | from niyam.mission.status import run_mission_status
   |
help: Remove unused import: `niyam.mission.planner.get_latest_mission_id`

F401 [*] `shutil` imported but unused
 --> tests/test_multi_runtime.py:7:8
  |
5 | import json
6 | import os
7 | import shutil
  |        ^^^^^^
8 | import subprocess
9 | from pathlib import Path
  |
help: Remove unused import: `shutil`

F401 [*] `subprocess` imported but unused
  --> tests/test_multi_runtime.py:8:8
   |
 6 | import os
 7 | import shutil
 8 | import subprocess
   |        ^^^^^^^^^^
 9 | from pathlib import Path
10 | from unittest.mock import patch, MagicMock
   |
help: Remove unused import: `subprocess`

F401 [*] `pytest` imported but unused
  --> tests/test_multi_runtime.py:12:8
   |
10 | from unittest.mock import patch, MagicMock
11 |
12 | import pytest
   |        ^^^^^^
13 | import yaml
14 | from rich.console import Console
   |
help: Remove unused import: `pytest`

F401 [*] `yaml` imported but unused
  --> tests/test_multi_runtime.py:13:8
   |
12 | import pytest
13 | import yaml
   |        ^^^^
14 | from rich.console import Console
   |
help: Remove unused import: `yaml`

F401 [*] `yaml` imported but unused
 --> tests/test_packs.py:8:8
  |
6 | from pathlib import Path
7 | import pytest
8 | import yaml
  |        ^^^^
9 | from rich.console import Console
  |
help: Remove unused import: `yaml`

F401 [*] `pytest` imported but unused
 --> tests/test_pr.py:7:8
  |
5 | import os
6 | from pathlib import Path
7 | import pytest
  |        ^^^^^^
8 | from rich.console import Console
9 | from unittest.mock import patch, MagicMock
  |
help: Remove unused import: `pytest`

F401 [*] `json` imported but unused
 --> tests/test_recovery.py:6:8
  |
5 | import os
6 | import json
  |        ^^^^
7 | from pathlib import Path
8 | from unittest.mock import patch, MagicMock
  |
help: Remove unused import: `json`

F401 [*] `pytest` imported but unused
  --> tests/test_recovery.py:9:8
   |
 7 | from pathlib import Path
 8 | from unittest.mock import patch, MagicMock
 9 | import pytest
   |        ^^^^^^
10 | import yaml
11 | from rich.console import Console
   |
help: Remove unused import: `pytest`

F401 [*] `yaml` imported but unused
  --> tests/test_recovery.py:10:8
   |
 8 | from unittest.mock import patch, MagicMock
 9 | import pytest
10 | import yaml
   |        ^^^^
11 | from rich.console import Console
   |
help: Remove unused import: `yaml`

F401 [*] `niyam.mission.executor.run_mission_start` imported but unused
  --> tests/test_recovery.py:16:5
   |
14 | from niyam.mission.planner import run_mission_plan, run_mission_approve
15 | from niyam.mission.executor import (
16 |     run_mission_start,
   |     ^^^^^^^^^^^^^^^^^
17 |     run_mission_retry,
18 |     run_mission_skip,
   |
help: Remove unused import: `niyam.mission.executor.run_mission_start`

F401 [*] `pytest` imported but unused
 --> tests/test_review.py:7:8
  |
5 | import os
6 | from pathlib import Path
7 | import pytest
  |        ^^^^^^
8 | from rich.console import Console
  |
help: Remove unused import: `pytest`

F401 [*] `pytest` imported but unused
 --> tests/test_run_composite.py:8:8
  |
6 | from pathlib import Path
7 | from typer.testing import CliRunner
8 | import pytest
  |        ^^^^^^
9 | import yaml
  |
help: Remove unused import: `pytest`

F401 [*] `yaml` imported but unused
  --> tests/test_run_composite.py:9:8
   |
 7 | from typer.testing import CliRunner
 8 | import pytest
 9 | import yaml
   |        ^^^^
10 |
11 | from niyam.cli import app
   |
help: Remove unused import: `yaml`

F401 [*] `unittest.mock.MagicMock` imported but unused
 --> tests/test_setup.py:7:34
  |
5 | import os
6 | from pathlib import Path
7 | from unittest.mock import patch, MagicMock
  |                                  ^^^^^^^^^
8 | import pytest
9 | from rich.console import Console
  |
help: Remove unused import: `unittest.mock.MagicMock`

F401 [*] `pytest` imported but unused
 --> tests/test_setup.py:8:8
  |
6 | from pathlib import Path
7 | from unittest.mock import patch, MagicMock
8 | import pytest
  |        ^^^^^^
9 | from rich.console import Console
  |
help: Remove unused import: `pytest`

F401 [*] `json` imported but unused
 --> tests/test_templates.py:6:8
  |
5 | import os
6 | import json
  |        ^^^^
7 | from pathlib import Path
8 | import pytest
  |
help: Remove unused import: `json`

F401 [*] `pytest` imported but unused
  --> tests/test_templates.py:8:8
   |
 6 | import json
 7 | from pathlib import Path
 8 | import pytest
   |        ^^^^^^
 9 | import yaml
10 | from rich.console import Console
   |
help: Remove unused import: `pytest`

F401 [*] `json` imported but unused
 --> tests/test_verification.py:6:8
  |
5 | import os
6 | import json
  |        ^^^^
7 | from pathlib import Path
8 | import pytest
  |
help: Remove unused import: `json`

Found 87 errors.
[*] 81 fixable with the `--fix` option (3 hidden fixes can be enabled with the `--unsafe-fixes` option).

```

## Validation Check - typecheck - 2026-05-30T06:22:52.008731Z
**Status:** ℹ SKIPPED — Not configured


## Validation Check - build - 2026-05-30T06:22:52.008794Z
**Status:** ℹ SKIPPED — Not configured


## Validation Run - 2026-05-30T06:23:06.373301Z
**Command:** `pytest`
**Exit Code:** `0`

### stdout
```
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.14/bin/python3.14
cachedir: .pytest_cache
rootdir: /Users/bhushan/Documents/Projects/niyam/.niyam/runs/requirements-utils-20260530-115223/worktrees/T1
configfile: pyproject.toml
testpaths: tests
plugins: cov-7.1.0, pytest_tmp_files-0.0.2, anyio-4.13.0
collecting ... collected 107 items

tests/test_ci.py::test_non_interactive_fails_unapproved PASSED           [  0%]
tests/test_ci.py::test_non_interactive_auto_approve PASSED               [  1%]
tests/test_ci.py::test_remote_policy_fetching PASSED                     [  2%]
tests/test_ci.py::test_remote_policy_fallback PASSED                     [  3%]
tests/test_ci.py::test_ci_verify_strict_missing_evidence PASSED          [  4%]
tests/test_ci.py::test_ci_verify_non_strict_missing_evidence PASSED      [  5%]
tests/test_ci.py::test_ci_verify_write_violation PASSED                  [  6%]
tests/test_cli.py::TestCLI::test_version PASSED                          [  7%]
tests/test_cli.py::TestCLI::test_help PASSED                             [  8%]
tests/test_cli.py::TestCLI::test_context_help PASSED                     [  9%]
tests/test_cli.py::TestCLI::test_guard_help PASSED                       [ 10%]
tests/test_cli.py::TestCLI::test_runtime_help PASSED                     [ 11%]
tests/test_cli.py::TestCLI::test_policy_help PASSED                      [ 12%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_architecture PASSED [ 13%]
tests/test_context.py::TestContextRefresh::test_context_refresh_creates_validation PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_python PASSED [ 14%]
tests/test_context.py::TestContextRefresh::test_context_refresh_detects_node PASSED [ 15%]
tests/test_context.py::TestContextRefresh::test_context_refresh_preserves_manual_section PASSED [ 16%]
tests/test_dashboard.py::test_dashboard_rendering PASSED                 [ 17%]
tests/test_dashboard.py::test_dashboard_watch_mode PASSED                [ 18%]
tests/test_doctor.py::TestDoctor::test_doctor_passes_on_fresh_init PASSED [ 19%]
tests/test_doctor.py::TestDoctor::test_doctor_fails_without_niyam PASSED [ 20%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_missing_files PASSED [ 21%]
tests/test_doctor.py::TestDoctor::test_doctor_detects_invalid_yaml PASSED [ 22%]
tests/test_doctor_enhanced.py::test_doctor_runtimes_in_path PASSED       [ 23%]
tests/test_doctor_enhanced.py::test_doctor_agents_validity PASSED        [ 24%]
tests/test_doctor_enhanced.py::test_doctor_validation_commands PASSED    [ 25%]
tests/test_doctor_enhanced.py::test_doctor_git_status_dirty PASSED       [ 26%]
tests/test_fleet.py::test_fleet_parallel_execution PASSED                [ 27%]
tests/test_fleet.py::test_fleet_dependency_failure PASSED                [ 28%]
tests/test_fleet.py::test_fleet_worktree_fallback_when_no_git PASSED     [ 28%]
tests/test_guard.py::TestGuard::test_guard_enable PASSED                 [ 29%]
tests/test_guard.py::TestGuard::test_guard_disable PASSED                [ 30%]
tests/test_guard.py::TestGuard::test_guard_careful_adds_warn_list PASSED [ 31%]
tests/test_guard.py::TestGuard::test_guard_freeze_adds_path PASSED       [ 32%]
tests/test_guard.py::TestGuard::test_guard_freeze_enables_guard PASSED   [ 33%]
tests/test_guardrails.py::test_path_write_denial_and_revert PASSED       [ 34%]
tests/test_hooks.py::test_hooks_lifecycle_triggers PASSED                [ 35%]
tests/test_init.py::TestInit::test_init_creates_niyam_directory PASSED   [ 36%]
tests/test_init.py::TestInit::test_init_creates_mvp_directories PASSED   [ 37%]
tests/test_init.py::TestInit::test_init_creates_niyam_yaml PASSED        [ 38%]
tests/test_init.py::TestInit::test_init_creates_agents PASSED            [ 39%]
tests/test_init.py::TestInit::test_init_creates_skills PASSED            [ 40%]
tests/test_init.py::TestInit::test_init_creates_commands PASSED          [ 41%]
tests/test_init.py::TestInit::test_init_creates_policies PASSED          [ 42%]
tests/test_init.py::TestInit::test_init_fails_if_already_exists PASSED   [ 42%]
tests/test_init.py::TestInit::test_init_force_overwrites PASSED          [ 43%]
tests/test_init.py::TestInit::test_init_dry_run_creates_nothing PASSED   [ 44%]
tests/test_init.py::TestInit::test_init_with_claude_runtime PASSED       [ 45%]
tests/test_init.py::TestInit::test_init_invalid_profile_fails PASSED     [ 46%]
tests/test_init.py::TestInit::test_init_backend_profile PASSED           [ 47%]
tests/test_init.py::TestInit::test_init_frontend_profile PASSED          [ 48%]
tests/test_memory.py::TestMemory::test_memory_show PASSED                [ 49%]
tests/test_memory.py::TestMemory::test_memory_add PASSED                 [ 50%]
tests/test_memory.py::TestMemory::test_memory_clear PASSED               [ 51%]
tests/test_memory.py::TestMemory::test_memory_sync_propagates_to_runtimes PASSED [ 52%]
tests/test_mission.py::TestMission::test_mission_plan_creates_files PASSED [ 53%]
tests/test_mission.py::TestMission::test_mission_approve PASSED          [ 54%]
tests/test_mission.py::TestMission::test_mission_execution_lifecycle PASSED [ 55%]
tests/test_mission.py::TestMission::test_mission_pause_resume PASSED     [ 56%]
tests/test_mission.py::TestMission::test_mission_plan_strict PASSED      [ 57%]
tests/test_multi_runtime.py::test_planner_prompt_contains_runtime PASSED [ 57%]
tests/test_multi_runtime.py::test_planner_parses_runtime_field PASSED    [ 58%]
tests/test_multi_runtime.py::test_executor_resolves_task_runtime PASSED  [ 59%]
tests/test_packs.py::TestPacks::test_list_packs PASSED                   [ 60%]
tests/test_packs.py::TestPacks::test_add_pack_copies_files PASSED        [ 61%]
tests/test_packs.py::TestPacks::test_add_pack_conflict PASSED            [ 62%]
tests/test_packs.py::TestPacks::test_remove_pack PASSED                  [ 63%]
tests/test_packs.py::TestPacks::test_sync_packs PASSED                   [ 64%]
tests/test_pr.py::test_pr_review_mocked PASSED                           [ 65%]
tests/test_pr.py::test_pr_create_mocked PASSED                           [ 66%]
tests/test_recovery.py::test_mission_skip_unblocks_downstream PASSED     [ 67%]
tests/test_recovery.py::test_mission_retry_requeues_tasks PASSED         [ 68%]
tests/test_recovery.py::test_mission_rollback_git_checkout PASSED        [ 69%]
tests/test_remediation.py::test_bash_sh_blocked PASSED                   [ 70%]
tests/test_remediation.py::test_report_fails_on_validation_failure PASSED [ 71%]
tests/test_remediation.py::test_context_diff_ignores_manual_sections PASSED [ 71%]
tests/test_remediation.py::test_claude_hook_script_formatting_and_imports PASSED [ 72%]
tests/test_remediation.py::test_validate_mission_plan_cycle PASSED       [ 73%]
tests/test_remediation.py::test_validate_mission_plan_unknown_dependency PASSED [ 74%]
tests/test_remediation.py::test_writes_files_false_violation_and_revert PASSED [ 75%]
tests/test_review.py::TestReview::test_get_git_diff_untracked_file PASSED [ 76%]
tests/test_review.py::TestReview::test_run_review_engineering_lens PASSED [ 77%]
tests/test_review.py::TestReview::test_run_review_adversarial_mode PASSED [ 78%]
tests/test_review.py::TestReview::test_get_git_diff_file_size_limit PASSED [ 79%]
tests/test_review.py::TestReview::test_get_git_diff_budget_limit PASSED  [ 80%]
tests/test_review.py::TestReview::test_get_git_diff_skip_binary_files PASSED [ 81%]
tests/test_review.py::TestReview::test_get_git_diff_redact_secrets PASSED [ 82%]
tests/test_run_composite.py::test_run_composite_command_file PASSED      [ 83%]
tests/test_run_composite.py::test_run_composite_command_inline_string PASSED [ 84%]
tests/test_setup.py::test_setup_wizard_fresh_initialization PASSED       [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_md PASSED [ 85%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_claude_dir PASSED [ 86%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_agents PASSED [ 87%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_hooks PASSED [ 88%]
tests/test_sync.py::TestClaudeSync::test_claude_sync_creates_settings PASSED [ 89%]
tests/test_sync.py::TestClaudeSync::test_claude_md_contains_policies PASSED [ 90%]
tests/test_sync.py::TestCodexSync::test_codex_sync_creates_agents_md PASSED [ 91%]
tests/test_sync.py::TestCodexSync::test_agents_md_contains_policies PASSED [ 92%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_md PASSED [ 93%]
tests/test_sync.py::TestGeminiSync::test_gemini_sync_creates_gemini_dir PASSED [ 94%]
tests/test_sync.py::TestGeminiSync::test_gemini_md_contains_policies PASSED [ 95%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_updates_config PASSED [ 96%]
tests/test_sync.py::TestRuntimeAdd::test_runtime_add_duplicate_is_safe PASSED [ 97%]
tests/test_templates.py::test_builtin_template_planning PASSED           [ 98%]
tests/test_templates.py::test_custom_template_planning PASSED            [ 99%]
tests/test_verification.py::test_verification_lifecycle PASSED           [100%]

=============================== warnings summary ===============================
tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:167: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    report_sections.append(f"- **Generated:** `{datetime.utcnow().isoformat()}Z`")

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:226: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "timestamp": datetime.utcnow().isoformat() + "Z",

tests/test_mission.py::TestMission::test_mission_execution_lifecycle
tests/test_verification.py::test_verification_lifecycle
  /Users/bhushan/Documents/Projects/niyam/niyam/mission/reporter.py:255: DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled for removal in a future version. Use timezone-aware objects to represent datetimes in UTC: datetime.datetime.now(datetime.UTC).
    "completed": datetime.utcnow().isoformat() + "Z",

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 107 passed, 6 warnings in 13.93s =======================

```
