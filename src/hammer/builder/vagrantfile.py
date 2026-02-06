"""Vagrantfile generation for HAMMER assignments."""

import shlex
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from hammer.spec import HammerSpec
from hammer.builder.network import NetworkPlan


# Template directory is relative to this module
TEMPLATES_DIR = Path(__file__).parent / "templates"


def render_vagrantfile(
    spec: HammerSpec,
    network: NetworkPlan,
    box_name: str = "generic/alma9",
) -> str:
    """
    Render a Vagrantfile from the spec and network plan.

    Args:
        spec: The HAMMER spec defining topology
        network: The resolved network plan with IP assignments
        box_name: Vagrant box to use (default: generic/alma9)

    Returns:
        Rendered Vagrantfile content as a string
    """
    env = Environment(
        loader=FileSystemLoader(TEMPLATES_DIR),
        keep_trailing_newline=True,
    )
    env.filters["shellescape"] = shlex.quote
    template = env.get_template("Vagrantfile.j2")

    return template.render(
        assignment_id=spec.assignment_id,
        box_name=box_name,
        nodes=spec.topology.nodes,
        network=network,
        domain=spec.topology.domain,
    )
