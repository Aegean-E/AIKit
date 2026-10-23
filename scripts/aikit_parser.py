"""
The `aikit` command-line grammar: its parser and the Why/Fix triad for usage errors.

Kept apart from scripts/aikit_cli.py so `python aikit.py --help` loads argparse and this module
instead of every module the commands use (PRINCIPLE-010 R5, ADR-180). It imports no AIKit module
at top level: ProjectError is imported inside TriadArgumentParser.error, and aikit_cli, which
imports this module and re-exports its names, is never imported here.
"""

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from scripts.project_registry import ProjectError

# The values scripts/disruption_recovery.py defines, mirrored rather than imported: importing it
# would load the module graph this file exists to avoid. tests/test_kit.py pins both to it.
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMP_STALE_SECONDS = 60


def report_error(error: "ProjectError") -> int:
    """Print the error triad to stderr and return its exit code."""
    print(f"Error: {error}", file=sys.stderr)
    print(f"Why: {error.why}", file=sys.stderr)
    print(f"Fix: {error.fix}", file=sys.stderr)
    return error.exit_code


class TriadArgumentParser(argparse.ArgumentParser):
    """argparse whose usage errors carry Why/Fix like every other AIKit error."""

    def error(self, message: str) -> NoReturn:
        # Imported on the one path that needs it, so `--help` stays light (ADR-180).
        from scripts.project_registry import ProjectError
        self.print_usage(sys.stderr)
        sys.exit(report_error(ProjectError(
            message,
            "the command line does not match any `aikit` command.",
            f"run `{self.prog} --help` to list the valid forms.",
            exit_code=2,
        )))


def build_parser() -> argparse.ArgumentParser:
    parser = TriadArgumentParser(
        prog="python aikit.py",
        description="Create and manage the projects AIKit builds. Each project is its own folder "
                    "and git repository with its memory in .aikit/.",
    )
    # Explicit, never guessed from the working directory: a stray `projects/` folder elsewhere
    # must not become the registry (ADR-128).
    parser.add_argument("--workspace", type=Path, default=ROOT_DIR, metavar="DIR",
                        help="AIKit checkout whose projects/ to use (default: this one; for sandboxes)")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=TriadArgumentParser)

    def project_command(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("name", help="project name, as `list` shows it")
        return sub

    new = commands.add_parser("new", help="create projects/<name>/ as a new git repository")
    new.add_argument("name", help="folder name: lowercase letters, digits, '-' or '_'")
    new.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")
    new.add_argument("--publish", action="store_true", help="publish to GitHub immediately after creation")
    new.add_argument("--public", action="store_true", help="make the GitHub repository public (default: private)")

    attach = commands.add_parser("attach", help="register an existing project folder")
    attach.add_argument("path", type=Path, help="the project's top folder")
    attach.add_argument("--name", help="project name (default: the folder name)")
    attach.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")

    commands.add_parser("list", help="show every project, its stacks and test command")
    status = project_command("status",
                             "a project's task, uncommitted work, latest decision and gates")
    status.add_argument("--exit-code", action="store_true",
                        help="exit 1 when the project is dirty, conflicted, has an open UI task, or cannot be audited")
    status.add_argument("--json", action="store_true",
                        help="print the report as JSON instead of text; `clean` is the --exit-code verdict")
    resume = project_command("resume", "the cold-start report for a project (PRINCIPLE-004 R2)")
    resume.add_argument("--json", action="store_true",
                        help="print the cold-start report as JSON instead of text")

    checkpoint = project_command("checkpoint", "record a checkpoint in the project's ledger")
    checkpoint.add_argument("--task", required=True, help="task ID")
    checkpoint.add_argument("--phase-num", type=int, required=True, choices=[1, 2, 3, 4, 5],
                            help="lifecycle phase 1-5")
    checkpoint.add_argument("--desc", required=True, help="what was done; a plan starts '[1/M]'")
    for field in ("why", "benefits", "risks", "mitigation"):
        checkpoint.add_argument(f"--{field}", default=None,
                                help="impact assessment, required on a task's first plan (PRINCIPLE-007 R6)")
    checkpoint.add_argument("--handoff", default="",
                            help="cold-start packet: 'next: ...' plus optional state, failed, "
                                 "open, evidence, separated by ';' (PRINCIPLE-004 R2)")
    checkpoint.add_argument("--redact", action="store_true",
                            help="record credential-shaped text as [REDACTED] instead of refusing it")

    complete = project_command("complete", "mark the project's active task completed")
    complete.add_argument("--task", required=True, help="the active task's ID")

    project_command("clean", f"delete the project's temp buffers older than {TEMP_STALE_SECONDS}s")
    guideline = project_command("guideline", "add a rule to the project's guidelines (below the principles)")
    guideline.add_argument("rule", help="the rule, one line")
    guideline.add_argument("--source", required=True, help="where it comes from: user, ADR-NNN or a person")

    check = project_command("check", "run every gate of a project (its Phase 4)")
    check.add_argument("--no-push", action="store_true", help="skip pushing commits to remote origin after gates pass")
    check.add_argument("--strict", action="store_true",
                       help="require a clean non-bookkeeping tree and a codebase map before passing")
    project_command("fix", "restore missing project memory and README, refresh its map, then check")
    publish = project_command("publish", "upload the project to its own GitHub repository (private by default)")
    publish.add_argument("--public", action="store_true", help="create the repository as public")

    ui = commands.add_parser("ui", help="bound edits to one UI surface declared in .aikit/ui.json")
    ui_commands = ui.add_subparsers(dest="ui_action", required=True, parser_class=TriadArgumentParser)
    for action, text in (("init", "write a UI contract (React/Vite auto, or --fast/--paths)"),
                         ("begin", "open a bounded task from a clean green baseline"),
                         ("verify", "check scope, budget, the fast and snapshot proofs, style"),
                         ("finish", "verify, then close the task (needs --reviewed)"),
                         ("allow", "record an intended inventory removal pattern"),
                         ("abort", "restore only the surface to its baseline"),
                         ("status", "show the open task and its changed paths")):
        sub = ui_commands.add_parser(action, help=text)
        sub.add_argument("name", help="project name, as `list` shows it")
        if action == "begin":
            sub.add_argument("--surface", required=True,
                             help="surface name declared in .aikit/ui.json")
        if action == "init":
            sub.add_argument("--surface", default="app",
                             help="surface name for the generated contract")
            sub.add_argument("--fast", default="",
                             help="manual proof command for a non-React/Vite stack")
            sub.add_argument("--paths", action="append", default=None,
                             help="surface path pattern for a manual contract; repeatable")
            sub.add_argument("--snapshot", default="",
                             help="optional inventory command for a manual contract")
        if action == "allow":
            sub.add_argument("pattern",
                             help="glob matching the inventory entries this task removes")
            sub.add_argument("--reason", required=True,
                             help="why the removal is intended; recorded with the allow entry")
        if action == "finish":
            sub.add_argument("--reviewed", action="store_true",
                             help="confirm a human looked at the running UI")
            sub.add_argument("--reviewer", metavar="NAME",
                             help="who reviewed the running UI, recorded in the task history")
        if action == "verify":
            sub.add_argument("--json", action="store_true",
                             help="emit stable finding codes as JSON for CI")


    delegate = commands.add_parser("delegate", help="run an OpenCode sub-agent on a bounded brief")
    delegate.add_argument("role", help="a profile name in .opencode/agents/")
    delegate.add_argument("prompt", help="the brief for the sub-agent")
    delegate.add_argument("--file", "-f", default=None, help="file to attach to the brief")
    delegate.add_argument("--project", "-p", default=None, help="run inside this registered project")
    delegate.add_argument("--model", "-m", default=None, help="model ID, e.g. ollama/qwen2.5-coder")
    delegate.add_argument("--timeout", type=int, default=120, help="seconds before the run is killed")
    delegate.add_argument("--format", choices=["text", "json"], default="text", help="report format")
    return parser
