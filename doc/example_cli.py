# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
"""An example script to demonstrate config-file option readout."""

# To improve loading performance, we recommend you only import the very
# essential packages needed to start the CLI.  Defer all other imports to
# within the function implementing the command.

import click

from clapper.click import ConfigCommand, ResourceOption, verbosity_option
from clapper.logging import setup

logger = setup(__name__.split(".", 1)[0])


@click.command(
    context_settings={
        "show_default": True,
        "help_option_names": ["-?", "-h", "--help"],
    },
    # if configuration 'modules' must be loaded from package entry-points,
    # then must search this entry-point group:
    entry_point_group="test.app",
    cls=ConfigCommand,
    epilog="""\b
Examples:

  $ test_app -vvv --integer=3
""",
)
@click.option("--integer", type=int, default=42, cls=ResourceOption)
@click.option("--flag/--no-flag", default=False, cls=ResourceOption)
@click.option("--str", default="foo", cls=ResourceOption)
@click.option(
    "--choice",
    type=click.Choice(["red", "green", "blue"]),
    cls=ResourceOption,
)
@verbosity_option(logger=logger)
@click.version_option(package_name="clapper")
@click.pass_context
def main(ctx, **_):
    """Test our Click interfaces."""
    # Add imports needed for your code here, and avoid spending time loading!

    # In this example, we just print the loaded options to demonstrate loading
    # from config files actually works!
    for k, v in ctx.params.items():
        if k in ("dump_config", "config"):
            continue
        click.echo(f"{k}: {v}")


if __name__ == "__main__":
    main()
