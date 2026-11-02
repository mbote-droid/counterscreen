"""Command line surface for counterscreen.

Thin dispatch only. Every subcommand delegates to a package under
``counterscreen``; no pipeline logic lives here. See DESIGN.md section 1.
"""

import typer

from counterscreen import __version__

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Specificity-first protein binder design and evaluation.",
)


@app.callback()
def _root() -> None:
    """Keep the application a command group.

    Typer promotes a lone command to the root callback, which would make
    ``counterscreen`` run that command instead of showing help. Subcommands
    arrive per package, so the group is declared up front.
    """


@app.command()
def version() -> None:
    """Print the installed counterscreen version."""
    typer.echo(__version__)


def main() -> None:
    """Entry point registered as the ``counterscreen`` console script."""
    app()


if __name__ == "__main__":
    main()
