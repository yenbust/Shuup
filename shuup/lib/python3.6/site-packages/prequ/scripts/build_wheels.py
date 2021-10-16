import os
import subprocess
from glob import glob

import click

from ..configuration import PrequConfiguration
from ..exceptions import PrequError, WheelMissing
from ..logging import log

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.option('-c', '--check', is_flag=True,
              help="Check if the wheels exists")
def main(silent, check):
    """
    Build wheels of required packages.
    """
    try:
        build_wheels(silent=silent, check_only=check)
    except PrequError as error:
        log.error('{}'.format(error))
        raise SystemExit(1)


def build_wheels(silent=False, check_only=False):
    conf = PrequConfiguration.from_directory('.')
    to_build = list(conf.get_wheels_to_build())
    for (pkg, ver, url) in to_build:
        build_wheel(conf, pkg, ver, url, silent, check_only)


def build_wheel(conf, pkg, ver, url, silent=False, check_only=False):
    info = log.info if not silent else (lambda x: None)
    already_built = get_wheels(conf, pkg, ver)
    if check_only:
        if already_built:
            info('{} exists'.format(already_built[0]))
            return
        raise WheelMissing('Wheel for {} {} is missing'.format(pkg, ver))
    if already_built:
        info('*** Already built: {}'.format(already_built[0]))
        return
    info('*** Building wheel for {} {} from {}'.format(pkg, ver, url))
    call('pip wheel {verbosity} -w {w} --no-deps {u}',
         verbosity=('-q' if silent else '-v'),
         w=conf.wheel_dir, u=url)
    built_wheel = get_wheels(conf, pkg, ver)[0]
    info('*** Built: {}'.format(built_wheel))
    for wheel in get_wheels(conf, pkg):  # All versions
        if wheel != built_wheel:
            info('*** Removing: {}'.format(wheel))
            os.remove(wheel)


def get_wheels(conf, pkg, ver='*'):
    return glob(os.path.join(
        conf.wheel_dir, '{}-{}-*.whl'.format(pkg.replace('-', '_'), ver)))


def call(cmd, stdout=None, **kwargs):
    formatted_cmd = [x.format(**kwargs) for x in cmd.split()]
    return subprocess.check_call(formatted_cmd, stdout=stdout)
