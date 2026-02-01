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

    args = parser.parse_args()

    if args.command == "validate":
        _cmd_validate(args)
    elif args.command == "build":
        _cmd_build(args)


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


if __name__ == "__main__":
    main()
