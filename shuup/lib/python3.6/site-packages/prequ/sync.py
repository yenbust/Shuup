import collections
import os
import sys
from subprocess import check_call

import click

from .exceptions import IncompatibleRequirements, UnsupportedConstraint
from .utils import (
    flat_map, format_requirement, is_pinned_requirement, is_vcs_link,
    key_from_dist, key_from_ireq, key_from_req)

PACKAGES_TO_IGNORE = [
    '-markerlib',
    'pip',
    'prequ',
    'pip-review',
    'pkg-resources',
    'setuptools',
    'wheel',
]


def dependency_tree(installed_keys, root_key):
    """
    Calculate the dependency tree for the package `root_key` and return
    a collection of all its dependencies.  Uses a DFS traversal algorithm.

    `installed_keys` should be a {key: requirement} mapping, e.g.
        {'django': from_line('django==1.8')}
    `root_key` should be the key to return the dependency tree for.
    """
    dependencies = set()
    queue = collections.deque()

    if root_key in installed_keys:
        dep = installed_keys[root_key]
        queue.append(dep)

    while queue:
        v = queue.popleft()
        if v.key in dependencies:
            continue

        dependencies.add(v.key)

        for dep_specifier in v.requires():
            dep_name = key_from_req(dep_specifier)
            if dep_name in installed_keys:
                dep = installed_keys[dep_name]

                specifier = dep_specifier.specifier
                if specifier.contains(dep.version, prereleases=True):
                    queue.append(dep)

    return dependencies


def get_dists_to_ignore(installed):
    """
    Returns a collection of package names to ignore when performing prequ sync,
    based on the currently installed environment.  For example, when Prequ
    is installed in the local environment, it should be ignored, including all
    of its dependencies (e.g. click).  When Prequ is not installed
    locally, click should also be installed/uninstalled depending on the given
    requirements.
    """
    installed_keys = {key_from_dist(r): r for r in installed}
    return list(flat_map(lambda req: dependency_tree(installed_keys, req), PACKAGES_TO_IGNORE))


def merge(requirements, ignore_conflicts):
    by_key = {}

    for ireq in requirements:
        if ((is_vcs_link(ireq) and not ireq.editable and not is_pinned_requirement(ireq))):
            msg = 'Prequ does not support non-editable vcs URLs that are not pinned to one version.'
            raise UnsupportedConstraint(msg, ireq)

        key = key_from_ireq(ireq)

        if not ignore_conflicts:
            existing_ireq = by_key.get(key)
            if existing_ireq:
                # NOTE: We check equality here since we can assume that the
                # requirements are all pinned
                if ireq.specifier != existing_ireq.specifier:
                    raise IncompatibleRequirements(ireq, existing_ireq)

        # TODO: Always pick the largest specifier in case of a conflict
        by_key[key] = ireq

    return by_key.values()


def diff(compiled_requirements, installed_dists):
    """
    Calculate which packages should be installed or uninstalled, given a set
    of compiled requirements and a list of currently installed modules.
    """
    requirements_lut = {key_from_ireq(r): r for r in compiled_requirements}

    satisfied = set()  # holds keys
    to_install = set()  # holds InstallRequirement objects
    to_uninstall = set()  # holds keys

    pkgs_to_ignore = get_dists_to_ignore(installed_dists)
    for dist in installed_dists:
        key = key_from_dist(dist)
        if key not in requirements_lut or not requirements_lut[key].match_markers():
            to_uninstall.add(dist.key)
        elif requirements_lut[key].specifier.contains(dist.version):
            satisfied.add(key)

    for key, requirement in requirements_lut.items():
        if key not in satisfied and requirement.match_markers():
            to_install.add(requirement)

    # Make sure to not uninstall any packages that should be ignored
    to_uninstall -= set(pkgs_to_ignore)

    return (to_install, to_uninstall)


def sync(to_install, to_uninstall,  # noqa: C901
         verbose=False, dry_run=False,
         pip_flags=None, install_flags=None):
    """
    Install and uninstalls the given sets of modules.
    """
    if not to_uninstall and not to_install:
        click.echo("Everything up-to-date")

    if pip_flags is None:
        pip_flags = []

    if not verbose:
        pip_flags += ['-q']

    if os.environ.get('VIRTUAL_ENV'):
        # find pip via PATH
        pip = 'pip'
    else:
        # find pip in same directory as prequ entry-point script
        pip = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'pip')

    if to_uninstall:
        if dry_run:
            click.echo("Would uninstall:")
            for pkg in to_uninstall:
                click.echo("  {}".format(pkg))
        else:
            check_call([pip, 'uninstall', '-y'] + pip_flags + sorted(to_uninstall))

    if to_install:
        if install_flags is None:
            install_flags = []
        if dry_run:
            click.echo("Would install:")
            for ireq in to_install:
                click.echo("  {}".format(format_requirement(ireq)))
        else:
            package_args = sum((
                _ireq_to_install_args(ireq)
                for ireq in sorted(to_install, key=key_from_ireq)), [])
            check_call([pip, 'install'] + pip_flags + install_flags + package_args)
    return 0


def _ireq_to_install_args(ireq):
    """
    :type ireq: pip.req.InstallRequirement
    """
    line = format_requirement(ireq, root_dir=None)
    if line.startswith('-e '):
        return ['-e', line[3:]]
    return [line]
