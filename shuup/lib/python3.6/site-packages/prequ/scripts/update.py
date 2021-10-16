import click

from . import build_wheels, compile

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.pass_context
def main(ctx, verbose, silent):
    """
    Build wheels and compile requirements.
    """
    ctx.invoke(build_wheels.main, silent=silent)
    ctx.invoke(compile.main, verbose=verbose, silent=silent)
