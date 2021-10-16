from pip import __version__ as pip_version
from pip._vendor.pkg_resources import Requirement, parse_version

PIP_9_OR_NEWER = (parse_version(pip_version) >= parse_version('9.0'))
PIP_10_OR_NEWER = (parse_version(pip_version) >= parse_version('10.0'))
PIP_18_OR_NEWER = (parse_version(pip_version) >= parse_version('18.0'))
PIP_192_OR_NEWER = (parse_version(pip_version) >= parse_version('19.2'))

try:
    from pip._internal.cli.base_command import Command
except ImportError:
    if PIP_10_OR_NEWER:
        from pip._internal.basecommand import Command
    else:
        from pip.basecommand import Command

try:
    from pip._internal.cli import cmdoptions
except ImportError:
    if PIP_10_OR_NEWER:
        from pip._internal import cmdoptions
    else:
        from pip import cmdoptions


if PIP_10_OR_NEWER:
    from pip._internal.cache import WheelCache
    from pip._internal.exceptions import InstallationError
    from pip._internal.operations.prepare import RequirementPreparer
    from pip._internal.req.req_install import InstallRequirement
    from pip._internal.req.req_file import parse_requirements
    from pip._internal.req.req_set import RequirementSet
    from pip._internal.utils.appdirs import user_cache_dir
    from pip._internal.utils.hashes import FAVORITE_HASH
    from pip._internal.download import is_file_url, path_to_url, url_to_path
    from pip._internal.index import FormatControl, PackageFinder
    from pip._internal.wheel import Wheel
    from pip._internal.utils.misc import get_installed_distributions
    from pip._internal.models.index import PyPI
else:
    from pip.exceptions import InstallationError
    from pip.req.req_install import InstallRequirement
    from pip.req.req_file import parse_requirements
    from pip.req.req_set import RequirementSet
    from pip.utils.appdirs import user_cache_dir
    from pip.utils.hashes import FAVORITE_HASH
    from pip.download import is_file_url, path_to_url, url_to_path
    from pip.index import FormatControl, PackageFinder
    from pip.wheel import Wheel, WheelCache
    from pip.utils import get_installed_distributions
    from pip.models.index import PyPI

    RequirementPreparer = None


if PIP_10_OR_NEWER:
    try:
        from pip._internal.resolve import Resolver
    except ImportError:
        from pip._internal.legacy_resolve import Resolver
else:
    Resolver = None


if PIP_18_OR_NEWER:
    from pip._internal.req.req_tracker import RequirementTracker
else:
    class RequirementTracker(object):
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass


try:
    from pip._internal.req.constructors import install_req_from_editable
except ImportError:
    install_req_from_editable = InstallRequirement.from_editable


try:
    from pip._internal.req.constructors import install_req_from_line
except ImportError:
    install_req_from_line = InstallRequirement.from_line


if not hasattr(PackageFinder, 'create'):
    create_package_finder = PackageFinder
else:
    try:
        from pip._internal.models.search_scope import SearchScope
        from pip._internal.models.selection_prefs import SelectionPreferences
    except ImportError:
        create_package_finder = PackageFinder.create
    else:
        def create_package_finder(**kwargs):
            find_links = kwargs.pop('find_links', None)
            index_urls = kwargs.pop('index_urls', None)
            allow_all_prereleases = kwargs.pop('allow_all_prereleases', None)
            if find_links is not None:
                kwargs.setdefault('search_scope', SearchScope(
                    find_links=find_links,
                    index_urls=index_urls,
                ))
            if allow_all_prereleases is not None:
                kwargs.setdefault('selection_prefs', SelectionPreferences(
                    allow_yanked=True,
                    allow_all_prereleases=allow_all_prereleases,
                ))

            return PackageFinder.create(**kwargs)


__all__ = [
    'Command',
    'FAVORITE_HASH',
    'FormatControl',
    'InstallRequirement',
    'InstallationError',
    'PIP_10_OR_NEWER',
    'PIP_18_OR_NEWER',
    'PIP_9_OR_NEWER',
    'PackageFinder',
    'PyPI',
    'Requirement',
    'RequirementPreparer',
    'RequirementSet',
    'RequirementTracker',
    'Resolver',
    'Wheel',
    'WheelCache',
    'cmdoptions',
    'create_package_finder',
    'get_installed_distributions',
    'install_req_from_editable',
    'install_req_from_line',
    'is_file_url',
    'parse_requirements',
    'path_to_url',
    'url_to_path',
    'user_cache_dir',
]
