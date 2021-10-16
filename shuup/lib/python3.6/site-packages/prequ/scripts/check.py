import click

from . import build_wheels, compile

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.pass_context
def main(ctx, verbose, silent):
    """
    Check if generated requirements are up-to-date.
    """
    ctx.invoke(build_wheels.main, check=True, silent=silent)
    ctx.invoke(compile.main, check=True, verbose=verbose, silent=silent)
