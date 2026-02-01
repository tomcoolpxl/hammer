import argparse
import sys
from pathlib import Path
from pydantic import ValidationError
from hammer.spec import load_spec_from_file

def main():
    parser = argparse.ArgumentParser(description="HAMMER: Hands-on Ansible Multi-node Machine Evaluation Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # hammer validate --spec <file>
    validate_parser = subparsers.add_parser("validate", help="Validate a spec file")
    validate_parser.add_argument("--spec", type=Path, required=True, help="Path to the assignment spec YAML")

    args = parser.parse_args()

    if args.command == "validate":
        try:
            print(f"Validating {args.spec}...")
            spec = load_spec_from_file(args.spec)
            print("✅ Spec is valid!")
            print(f"Assignment ID: {spec.assignment_id}")
            print(f"Nodes: {[n.name for n in spec.topology.nodes]}")
        except ValidationError as e:
            print("❌ Validation Error:")
            print(e)
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
