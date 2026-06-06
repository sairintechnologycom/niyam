"""Niyam GitHub Pull Request Integration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from niyam.core.config import get_niyam_dir
from niyam.mission.planner import resolve_mission_id


def get_github_repo_owner_name(repo_root: Path) -> tuple[str, str] | None:
    """Extract owner and repo name from git remote origin URL."""
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        url = res.stdout.strip()
        if "github.com" in url:
            part = url.split("github.com")[-1]
            part = part.lstrip(":/")
            if part.endswith(".git"):
                part = part[:-4]
            parts = part.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
    except Exception:
        pass
    return None


def fetch_pr_diff_api(owner: str, repo: str, pr_id: str, token: str) -> str:
    """Fetch PR diff via raw GitHub REST API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_id}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3.diff")
    req.add_header("User-Agent", "Niyam-CLI")
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"GitHub API returned HTTP {e.code}: {e.read().decode('utf-8')}"
        )
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch PR diff from GitHub API: {e}")


def fetch_pr_diff_gh(pr_id: str, repo_root: Path) -> str:
    """Fetch PR diff using gh CLI."""
    if not shutil.which("gh"):
        raise RuntimeError(
            "GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set."
        )
    res = subprocess.run(
        ["gh", "pr", "diff", pr_id], cwd=repo_root, capture_output=True, text=True
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"GitHub CLI failed to fetch PR diff:\n{res.stderr or res.stdout}"
        )
    return res.stdout


def fetch_pr_body_api(owner: str, repo: str, pr_id: str, token: str) -> str:
    """Fetch PR body via raw GitHub REST API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_id}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"token {token}")
    req.add_header("User-Agent", "Niyam-CLI")
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("body", "")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to fetch PR body from GitHub API: {e}")


def fetch_pr_body_gh(pr_id: str, repo_root: Path) -> str:
    """Fetch PR body using gh CLI."""
    if not shutil.which("gh"):
        raise RuntimeError("GitHub CLI ('gh') is not installed.")
    res = subprocess.run(
        ["gh", "pr", "view", pr_id, "--json", "body", "-q", ".body"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"GitHub CLI failed to fetch PR body:\n{res.stderr}")
    return res.stdout.strip()


def get_pr_body(pr_id: str, token: str | None, repo_root: Path) -> str:
    """Retrieve PR body using API or gh CLI fallback."""
    token = token or os.environ.get("GITHUB_TOKEN")
    owner_repo = get_github_repo_owner_name(repo_root)
    if token and owner_repo:
        owner, repo = owner_repo
        try:
            return fetch_pr_body_api(owner, repo, pr_id, token)
        except Exception:
            return fetch_pr_body_gh(pr_id, repo_root)
    else:
        return fetch_pr_body_gh(pr_id, repo_root)


def get_pr_diff(pr_id: str, token: str | None, repo_root: Path) -> str:
    """Retrieve PR diff using API or gh CLI fallback."""
    token = token or os.environ.get("GITHUB_TOKEN")
    owner_repo = get_github_repo_owner_name(repo_root)
    if token and owner_repo:
        owner, repo = owner_repo
        try:
            return fetch_pr_diff_api(owner, repo, pr_id, token)
        except Exception as e:
            try:
                return fetch_pr_diff_gh(pr_id, repo_root)
            except Exception:
                raise e
    else:
        return fetch_pr_diff_gh(pr_id, repo_root)


def post_pr_comment_api(
    owner: str, repo: str, pr_id: str, token: str, body: str
) -> None:
    """Post comment to PR using raw GitHub REST API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_id}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Niyam-CLI")
    try:
        with urllib.request.urlopen(req) as response:
            if response.status not in (200, 201):
                raise RuntimeError(f"HTTP error {response.status}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to post comment via GitHub API: {e}")


def post_pr_comment_gh(pr_id: str, body: str, repo_root: Path) -> None:
    """Post comment to PR using gh CLI."""
    if not shutil.which("gh"):
        raise RuntimeError(
            "GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set."
        )
    res = subprocess.run(
        ["gh", "pr", "comment", pr_id, "--body", body],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"GitHub CLI failed to post comment:\n{res.stderr or res.stdout}"
        )


def post_pr_comment(pr_id: str, body: str, token: str | None, repo_root: Path) -> None:
    """Post comment using API or gh CLI fallback."""
    token = token or os.environ.get("GITHUB_TOKEN")
    owner_repo = get_github_repo_owner_name(repo_root)
    if token and owner_repo:
        owner, repo = owner_repo
        try:
            post_pr_comment_api(owner, repo, pr_id, token, body)
        except Exception as e:
            try:
                post_pr_comment_gh(pr_id, body, repo_root)
            except Exception:
                raise e
    else:
        post_pr_comment_gh(pr_id, body, repo_root)


def create_pr_api(
    owner: str, repo: str, title: str, body: str, head: str, base: str, token: str
) -> str:
    """Create a pull request via raw GitHub REST API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    data = json.dumps(
        {"title": title, "body": body, "head": head, "base": base}
    ).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"token {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Niyam-CLI")
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data.get("html_url", "")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to create PR via GitHub API: {e}")


def create_pr_gh(title: str, body: str, base: str, repo_root: Path, labels: list[str] | None = None) -> str:
    """Create a pull request using gh CLI."""
    if not shutil.which("gh"):
        raise RuntimeError(
            "GitHub CLI ('gh') is not installed and GITHUB_TOKEN is not set."
        )
    
    cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base]
    if labels:
        for label in labels:
            cmd.extend(["--label", label])

    res = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"GitHub CLI failed to create PR:\n{res.stderr or res.stdout}"
        )
    return res.stdout.strip()


def run_pr_review(
    pr_id: str,
    lens: str,
    runtime: str,
    mode: str,
    token: str | None,
    console: Console,
) -> None:
    """Fetch PR diff, perform code review, and post comment back to PR."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    # 1. Fetch review content
    review_content = ""
    if lens == "evidence":
        console.print(f"[cyan]Collecting evidence for review...[/]")
        mission_id = resolve_mission_id(niyam_dir)
        
        # Try local first
        evidence_path = None
        if mission_id:
            evidence_path = niyam_dir / "runs" / mission_id / "evidence.md"
        
        if evidence_path and evidence_path.exists():
            console.print("[dim]Using local evidence report.[/]")
            review_content = evidence_path.read_text(encoding="utf-8")
        else:
            # Try to fetch from PR body
            console.print("[cyan]Local evidence not found. Fetching from PR description...[/]")
            try:
                pr_body = get_pr_body(pr_id, token, repo_root)
                if "<details>" in pr_body and "</details>" in pr_body:
                    review_content = pr_body.split("<details>")[1].split("</details>")[0]
                    # Clean up summary and potential extra tags
                    if "<summary>" in review_content:
                        review_content = review_content.split("</summary>", 1)[1].strip()
                elif "## Niyam Mission Evidence" in pr_body:
                    review_content = pr_body.split("## Niyam Mission Evidence")[1].strip()
                
                if not review_content:
                    # Fallback: if nothing else, maybe the mission id is in the body
                    console.print("[yellow]Warning: Could not extract structured evidence from PR body.[/]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to fetch PR body: {e}[/]")

        if not review_content and mission_id:
            console.print("[yellow]Generating fresh local evidence...[/]")
            from niyam.mission.reporter import run_mission_report
            try:
                run_mission_report(console=console, mission_id=mission_id)
                if evidence_path and evidence_path.exists():
                    review_content = evidence_path.read_text(encoding="utf-8")
            except Exception:
                pass
    else:
        console.print(f"[cyan]Fetching diff for Pull Request #{pr_id}...[/]")
        review_content = get_pr_diff(pr_id, token, repo_root)

    if not review_content:
        console.print("[yellow]No content found to review.[/]")
        return

    # 2. Get template
    reviews_dir = Path(__file__).parent.parent / "templates" / "reviews"
    template_path = reviews_dir / f"{lens}.md"
    if not template_path.exists():
        raise FileNotFoundError(f"Review template for lens '{lens}' not found.")

    template_content = template_path.read_text(encoding="utf-8")

    # Apply mode modifications
    prefix = ""
    if mode == "adversarial":
        prefix = (
            "> [!WARNING]\n"
            "> **ADVERSARIAL MODE ENABLED**\n"
            "> You are acting as an adversarial, highly critical reviewer. "
            "Aggressively seek out bugs, race conditions, design flaws, styling inconsistencies, and security issues. "
            "Do not accept compromises. Critique every line of the content below.\n\n"
        )

    if lens == "evidence":
        compiled_prompt = prefix + template_content.replace("{{evidence_content}}", review_content)
    else:
        compiled_prompt = prefix + template_content.replace("{{git_diff}}", review_content)

    # 3. Save to a temporary prompt file for runtime reference
    runs_dir = niyam_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = runs_dir / f"review-pr-{pr_id}-{lens}-{mode}-prompt.md"
    prompt_file.write_text(compiled_prompt, encoding="utf-8")

    is_test = os.environ.get("NIYAM_TEST") == "1"
    review_output = ""

    if is_test:
        console.print("[dim]Mocking review execution...[/]")
        review_output = (
            f"Mocked structured code review for PR #{pr_id} using {lens} lens."
        )
    else:
        if shutil.which(runtime):
            console.print(f"[cyan]Invoking {runtime} CLI for PR review...[/]")
            output_file = runs_dir / f"review-pr-{pr_id}-{lens}-{mode}-output.txt"
            try:
                with open(output_file, "w", encoding="utf-8") as out_f:
                    subprocess.run(
                        [runtime, str(prompt_file)],
                        cwd=repo_root,
                        stdin=subprocess.DEVNULL,
                        stdout=out_f,
                        stderr=out_f,
                        check=True,
                    )
                review_output = output_file.read_text(encoding="utf-8")
            except Exception as e:
                console.print(f"[yellow]Warning: {runtime} execution failed: {e}[/]")
                console.print("Using fallback manual input...")
                review_output = "No automatic review response captured."
        else:
            console.print(f"[yellow]CLI '{runtime}' not found in PATH.[/]")
            console.print("Please copy the prompt and complete manually:")
            console.print(compiled_prompt)
            raise RuntimeError(f"Orchestrator '{runtime}' not found.")

    # 4. Post comment
    console.print(f"[cyan]Posting review comment to Pull Request #{pr_id}...[/]")
    post_pr_comment(pr_id, review_output, token, repo_root)
    console.print(
        f"[bold green]✓[/] Code review comment successfully posted to PR #{pr_id}."
    )


def run_pr_create(
    title: str,
    body: str | None,
    base: str,
    token: str | None,
    console: Console,
) -> None:
    """Push branch, extract evidence report, and create GitHub PR."""
    from niyam.core.config import find_niyam_root
    from niyam.core.errors import NiyamConfigError

    repo_root = find_niyam_root()
    if not repo_root:
        raise NiyamConfigError("Not a Niyam workspace. Run 'niyam init' first.")
    niyam_dir = get_niyam_dir(repo_root)

    # Get active branch name
    res = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    branch_name = res.stdout.strip()
    if branch_name == "HEAD":
        raise RuntimeError("HEAD is detached. Cannot create a pull request.")

    # 1. Push branch
    console.print(f"[cyan]Pushing branch '{branch_name}' to remote origin...[/]")
    is_test = os.environ.get("NIYAM_TEST") == "1"
    if not is_test:
        res_push = subprocess.run(
            ["git", "push", "-u", "origin", branch_name],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if res_push.returncode != 0:
            raise RuntimeError(f"Failed to push branch to remote:\n{res_push.stderr}")

    # 2. Get evidence report
    evidence_content = ""
    evidence_json = {}
    mission_id = resolve_mission_id(niyam_dir)
    if mission_id:
        run_dir = niyam_dir / "runs" / mission_id
        evidence_path = run_dir / "evidence.md"
        evidence_json_path = run_dir / "evidence.json"

        if not evidence_path.exists():
            console.print(
                "[yellow]Evidence report not found. Generating it automatically...[/]"
            )
            from niyam.mission.reporter import run_mission_report

            run_mission_report(console=console)

        if evidence_path.exists():
            evidence_content = evidence_path.read_text(encoding="utf-8")
        
        if evidence_json_path.exists():
            try:
                evidence_json = json.loads(evidence_json_path.read_text(encoding="utf-8"))
            except Exception:
                pass

    # Build concise PR body
    status_text = evidence_json.get("status", "unknown").upper()
    orchestrator = evidence_json.get("orchestrator", "unknown")
    task_count = len(evidence_json.get("tasks", []))
    completed_tasks = sum(1 for t in evidence_json.get("tasks", []) if t.get("status") == "completed")

    pr_summary = [
        f"## Niyam Mission Summary: {mission_id}",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| **Status** | {status_text} |",
        f"| **Orchestrator** | {orchestrator} |",
        f"| **Tasks** | {completed_tasks} / {task_count} completed |",
        f"| **Generated** | {evidence_json.get('completed', 'unknown')} |",
        "",
    ]

    # Extract integrity manifest if present
    integrity_block = ""
    if "## Cryptographic Integrity Manifest" in evidence_content:
        parts = evidence_content.split("## Cryptographic Integrity Manifest")
        if len(parts) > 1:
            integrity_block = "## Cryptographic Integrity Manifest" + parts[1].split("##")[0]
            # Remove integrity block from full content to avoid duplication
            evidence_content = parts[0] + (("##" + parts[1].split("##", 1)[1]) if len(parts[1].split("##")) > 1 else "")

    pr_body = body or "Pull Request automatically created by Niyam."
    pr_body += "\n\n" + "\n".join(pr_summary)

    if integrity_block:
        pr_body += "\n" + integrity_block.strip() + "\n"

    # Embed full evidence.json as a hidden comment for programmatic retrieval
    if evidence_json:
        pr_body += f"\n<!-- NIYAM_EVIDENCE_JSON_START\n{json.dumps(evidence_json)}\nNIYAM_EVIDENCE_JSON_END -->\n"

    if evidence_content:
        pr_body += "\n<details>\n<summary>Click to expand full Evidence Package</summary>\n\n"
        pr_body += evidence_content.strip()
        pr_body += "\n\n</details>\n"

    # 3. Create PR
    console.print(
        f"[cyan]Creating Pull Request for branch '{branch_name}' targeting '{base}'...[/]"
    )
    pr_url = ""
    labels = ["niyam-governed"]
    if status_text == "COMPLETED":
        labels.append("niyam-go")
    elif status_text == "FAILED":
        labels.append("niyam-no-go")

    if is_test:
        console.print("[dim]Mocking PR creation...[/]")
        pr_url = "https://github.com/mock/repo/pull/42"
    else:
        token = token or os.environ.get("GITHUB_TOKEN")
        owner_repo = get_github_repo_owner_name(repo_root)
        if token and owner_repo:
            owner, repo = owner_repo
            try:
                # API doesn't support labels in PR creation easily, but we'll try gh first
                if shutil.which("gh"):
                    pr_url = create_pr_gh(title, pr_body, base, repo_root, labels=labels)
                else:
                    pr_url = create_pr_api(
                        owner, repo, title, pr_body, branch_name, base, token
                    )
            except Exception as e:
                try:
                    pr_url = create_pr_gh(title, pr_body, base, repo_root, labels=labels)
                except Exception:
                    raise e
        else:
            pr_url = create_pr_gh(title, pr_body, base, repo_root, labels=labels)

    console.print(
        Panel(
            f"[bold green]✓ Pull Request Created Successfully![/]\n[cyan]{pr_url}[/]",
            title="[bold green]PR Created[/]",
            border_style="green",
        )
    )
