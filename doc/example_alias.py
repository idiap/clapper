# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
"""An example script to demonstrate config-file option readout."""

# To improve loading performance, we recommend you only import the very
# essential packages needed to start the CLI.  Defer all other imports to
# within the function implementing the command.

import clapper.click
import click


@click.group(cls=clapper.click.AliasedGroup)
def main():
    """Declare main command-line application."""
    pass


@main.command()
def push():
    """Push subcommand."""
    click.echo("push was called")


@main.command()
def pop():
    """Pop subcommand."""
    click.echo("pop was called")


if __name__ == "__main__":
    main()
