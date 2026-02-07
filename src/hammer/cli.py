import argparse
import subprocess
import sys
from pathlib import Path
from pydantic import ValidationError

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from hammer.spec import load_spec_from_file
from hammer.prerequisites import check_prerequisites


console = Console()


def _format_validation_error(e: ValidationError, spec_path: Path) -> str:
    """Format a Pydantic ValidationError into user-friendly output."""
    lines = [f"Validation failed for spec: {spec_path}\n"]
    for error in e.errors():
        loc = " -> ".join(str(p) for p in error["loc"]) if error["loc"] else "(root)"
        msg = error["msg"]
        lines.append(f"  {loc}: {msg}")

        # Add contextual hints
        err_type = error.get("type", "")
        if "value_error" in err_type and "identifier" in msg.lower():
            lines.append("    Hint: identifiers must start with a letter and contain only [a-zA-Z0-9_-]")
        elif "value_error" in err_type and "path" in msg.lower():
            lines.append("    Hint: paths must not contain '..' or shell metacharacters")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="HAMMER: Hands-on Ansible Multi-node Machine Evaluation Runner"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # hammer validate --spec <file>
    validate_parser = subparsers.add_parser("validate", help="Validate a spec file")
    validate_parser.add_argument(
        "--spec", type=Path, required=True, help="Path to the assignment spec YAML"
    )

    # hammer build --spec <file> --out <dir>
    build_parser = subparsers.add_parser("build", help="Build assignment bundles")
    build_parser.add_argument(
        "--spec", type=Path, required=True, help="Path to the assignment spec YAML"
    )
    build_parser.add_argument(
        "--out", type=Path, required=True, help="Output directory for bundles"
    )
    build_parser.add_argument(
        "--box-version",
        type=str,
        default="generic/alma9",
        help="Vagrant box to use (default: generic/alma9)",
    )

    # hammer grade --spec <file> --student-repo <dir> --out <dir>
    grade_parser = subparsers.add_parser("grade", help="Grade a student submission")
    grade_parser.add_argument(
        "--spec", type=Path, required=True, help="Path to the assignment spec YAML"
    )
    grade_parser.add_argument(
        "--student-repo", type=Path, required=True, help="Path to student submission"
    )
    grade_parser.add_argument(
        "--out", type=Path, required=True, help="Output directory for results"
    )
    grade_parser.add_argument(
        "--grading-bundle", type=Path,
        help="Path to existing grading bundle with running VMs"
    )
    grade_parser.add_argument(
        "--phase",
        type=str,
        choices=["baseline", "mutation", "idempotence"],
        action="append",
        help="Run only specific phase(s) (can be repeated)",
    )
    grade_parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip regenerating grading bundle (use existing)",
    )
    grade_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Check prerequisites
    missing = check_prerequisites(args.command)
    if missing:
        console.print("[red]Missing prerequisites:[/red]")
        for msg in missing:
            console.print(f"  [yellow]{msg}[/yellow]")
        sys.exit(1)

    if args.command == "validate":
        _cmd_validate(args)
    elif args.command == "build":
        _cmd_build(args)
    elif args.command == "grade":
        _cmd_grade(args)


def _cmd_validate(args):
    """Handle the validate subcommand."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description=f"Validating {args.spec}...", total=None)
            spec = load_spec_from_file(args.spec)

        console.print("[green]Spec is valid![/green]")
        console.print(f"  Assignment ID: [cyan]{spec.assignment_id}[/cyan]")
        console.print(f"  Nodes: [cyan]{[n.name for n in spec.topology.nodes]}[/cyan]")

    except ValidationError as e:
        console.print("[red]Validation Error:[/red]")
        console.print(_format_validation_error(e, args.spec))
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _cmd_build(args):
    """Handle the build subcommand."""
    from hammer.builder import build_assignment

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Loading spec...", total=None)
            spec = load_spec_from_file(args.spec)

            progress.update(task, description="Building assignment bundles...")
            lock = build_assignment(
                spec=spec,
                output_dir=args.out,
                box_version=args.box_version,
                spec_dir=args.spec.parent,
            )

        console.print("[green]Build complete![/green]")
        console.print(f"  Student bundle: [cyan]{args.out / 'student_bundle'}[/cyan]")
        console.print(f"  Grading bundle: [cyan]{args.out / 'grading_bundle'}[/cyan]")
        console.print(f"  Lock file: [cyan]{args.out / 'lock.json'}[/cyan]")
        console.print(f"  Spec hash: [dim]{lock.spec_hash[:16]}...[/dim]")
        console.print(f"  Network: [cyan]{lock.resolved_network.cidr}[/cyan]")

    except ValidationError as e:
        console.print("[red]Validation Error:[/red]")
        console.print(_format_validation_error(e, args.spec))
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _cmd_grade(args):
    """Handle the grade subcommand."""
    from hammer.runner import grade_assignment

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task(description="Loading spec...", total=None)
            spec = load_spec_from_file(args.spec)
            progress.update(task, description="Grading student submission...")

        console.print(f"Grading [cyan]{args.student_repo}[/cyan]")
        console.print(f"Results: [cyan]{args.out}[/cyan]\n")

        # Determine phases to run
        phases = args.phase if args.phase else None

        report = grade_assignment(
            spec=spec,
            student_repo=args.student_repo,
            output_dir=args.out,
            phases=phases,
            grading_bundle=args.grading_bundle,
            skip_build=args.skip_build,
            verbose=args.verbose,
        )

        # Create results table
        table = Table(
            title="Grading Results",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold",
        )
        table.add_column("Phase", style="cyan")
        table.add_column("Converge", justify="center")
        table.add_column("Tests", justify="center")
        table.add_column("Score", justify="right")

        for phase_name, phase_result in report.phases.items():
            # Converge status
            if phase_result.converge.success:
                converge_status = "[green]PASS[/green]"
            else:
                converge_status = "[red]FAIL[/red]"

            converge_details = (
                f"{converge_status}\n"
                f"[dim]ok={phase_result.converge.ok} "
                f"changed={phase_result.converge.changed} "
                f"failed={phase_result.converge.failed}[/dim]"
            )

            # Tests status
            if phase_result.tests.failed == 0:
                tests_status = f"[green]{phase_result.tests.passed} passed[/green]"
            else:
                tests_status = (
                    f"[green]{phase_result.tests.passed} passed[/green], "
                    f"[red]{phase_result.tests.failed} failed[/red]"
                )

            # Score
            score_pct = (phase_result.score / phase_result.max_score * 100
                        if phase_result.max_score > 0 else 0)
            if score_pct >= 90:
                score_style = "green"
            elif score_pct >= 70:
                score_style = "yellow"
            else:
                score_style = "red"

            score_text = (
                f"[{score_style}]{phase_result.score:.1f}[/{score_style}] / "
                f"{phase_result.max_score:.1f}"
            )

            table.add_row(
                phase_name.upper(),
                converge_details,
                tests_status,
                score_text,
            )

        console.print(table)

        # Summary panel
        overall_status = "[green]PASS[/green]" if report.success else "[red]FAIL[/red]"
        score_pct = report.percentage
        if score_pct >= 90:
            score_style = "green"
        elif score_pct >= 70:
            score_style = "yellow"
        else:
            score_style = "red"

        summary = (
            f"Assignment: [cyan]{report.assignment_id}[/cyan]\n"
            f"Overall: {overall_status}\n"
            f"Total Score: [{score_style}]{report.total_score:.1f}[/{score_style}] / "
            f"{report.max_score:.1f} ([{score_style}]{report.percentage:.1f}%[/{score_style}])\n\n"
            f"Detailed report: [dim]{args.out / 'results' / 'report.json'}[/dim]"
        )

        console.print(Panel(summary, title="Summary", box=box.ROUNDED))

        if not report.success:
            sys.exit(1)

    except ValidationError as e:
        console.print("[red]Validation Error:[/red]")
        console.print(_format_validation_error(e, args.spec))
        sys.exit(1)
    except subprocess.CalledProcessError:
        console.print("[red]Execution failed.[/red]")
        console.print("[yellow]Recovery suggestions:[/yellow]")
        console.print("  1. Check VM status: vagrant status")
        console.print("  2. Destroy and recreate: vagrant destroy -f && vagrant up")
        console.print("  3. Check Ansible connectivity: ansible all -m ping")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
