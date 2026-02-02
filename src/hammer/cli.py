import argparse
import sys
from pathlib import Path
from pydantic import ValidationError
from hammer.spec import load_spec_from_file


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

    if args.command == "validate":
        _cmd_validate(args)
    elif args.command == "build":
        _cmd_build(args)
    elif args.command == "grade":
        _cmd_grade(args)


def _cmd_validate(args):
    """Handle the validate subcommand."""
    try:
        print(f"Validating {args.spec}...")
        spec = load_spec_from_file(args.spec)
        print("Spec is valid!")
        print(f"Assignment ID: {spec.assignment_id}")
        print(f"Nodes: {[n.name for n in spec.topology.nodes]}")
    except ValidationError as e:
        print("Validation Error:")
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def _cmd_build(args):
    """Handle the build subcommand."""
    from hammer.builder import build_assignment

    try:
        print(f"Loading spec from {args.spec}...")
        spec = load_spec_from_file(args.spec)

        print(f"Building assignment bundles in {args.out}...")
        lock = build_assignment(
            spec=spec,
            output_dir=args.out,
            box_version=args.box_version,
        )

        print("Build complete!")
        print(f"  Student bundle: {args.out / 'student_bundle'}")
        print(f"  Grading bundle: {args.out / 'grading_bundle'}")
        print(f"  Lock file: {args.out / 'lock.json'}")
        print(f"  Spec hash: {lock.spec_hash[:16]}...")
        print(f"  Network: {lock.resolved_network.cidr}")

    except ValidationError as e:
        print("Validation Error:")
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def _cmd_grade(args):
    """Handle the grade subcommand."""
    from hammer.runner import grade_assignment

    try:
        print(f"Loading spec from {args.spec}...")
        spec = load_spec_from_file(args.spec)

        print(f"Grading student submission from {args.student_repo}...")
        print(f"Results will be written to {args.out}")

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

        print("\n" + "=" * 60)
        print("GRADING COMPLETE")
        print("=" * 60)
        print(f"Assignment: {report.assignment_id}")
        print(f"Overall: {'PASS' if report.success else 'FAIL'}")
        print()

        for phase_name, phase_result in report.phases.items():
            status = "PASS" if phase_result.converge.success else "FAIL"
            print(f"  {phase_name}: {status}")
            print(f"    Converge: ok={phase_result.converge.ok}, "
                  f"changed={phase_result.converge.changed}, "
                  f"failed={phase_result.converge.failed}")
            print(f"    Tests: {phase_result.tests.passed} passed, "
                  f"{phase_result.tests.failed} failed")
            print(f"    Score: {phase_result.score:.1f} / {phase_result.max_score:.1f}")

        print()
        print(f"Total Score: {report.total_score:.1f} / {report.max_score:.1f} "
              f"({report.percentage:.1f}%)")
        print(f"\nDetailed report: {args.out / 'results' / 'report.json'}")

        if not report.success:
            sys.exit(1)

    except ValidationError as e:
        print("Validation Error:")
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
