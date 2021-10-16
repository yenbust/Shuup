# coding: utf-8
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

import json
import os
import sys

from ._pip_compat import Requirement
from .exceptions import PrequError
from .locations import CACHE_DIR
from .utils import as_tuple, key_from_req, lookup_table, name_from_ireq


class CorruptCacheError(PrequError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        lines = [
            'The dependency cache seems to have been corrupted.',
            'Inspect, or delete, the following file:',
            '  {}'.format(self.path),
        ]
        return os.linesep.join(lines)


def read_cache_file(cache_file_path):
    with open(cache_file_path, 'r') as cache_file:
        try:
            doc = json.load(cache_file)
        except ValueError:
            raise CorruptCacheError(cache_file_path)

        # Check version and load the contents
        assert doc['__format__'] == 1, 'Unknown cache file format'
        return doc['dependencies']


class DependencyCache(object):
    """
    Creates a new persistent dependency cache for the current Python version.
    The cache file is written to the appropriate user cache dir for the
    current platform, i.e.

        ~/.cache/prequ/depcache-pyX.Y.json

    Where X.Y indicates the Python version.
    """
    def __init__(self, cache_dir=None):
        if cache_dir is None:
            cache_dir = CACHE_DIR
        if not os.path.isdir(cache_dir):
            os.makedirs(cache_dir)
        py_version = '.'.join(str(digit) for digit in sys.version_info[:2])
        cache_filename = 'depcache-py{}.json'.format(py_version)

        self._cache_file = os.path.join(cache_dir, cache_filename)
        self._cache = None

    @property
    def cache(self):
        """
        The dictionary that is the actual in-memory cache.  This property
        lazily loads the cache from disk.
        """
        if self._cache is None:
            self.read_cache()
        return self._cache

    def as_cache_key(self, ireq):
        """
        Given a requirement, return its cache key. This behavior is a little weird in order to allow backwards
        compatibility with cache files. For a requirement without extras, this will return, for example:

        ("ipython", "2.1.0")

        For a requirement with extras, the extras will be comma-separated and appended to the version, inside brackets,
        like so:

        ("ipython", "2.1.0[nbconvert,notebook]")
        """
        name, version, extras = as_tuple(ireq)
        if not version:
            if not ireq.link:
                raise ValueError((
                    "Cannot cache dependencies of unpinned non-link "
                    "requirement: {}").format(ireq))
            version = ':UNPINNED:'
        if not extras:
            extras_string = ""
        else:
            extras_string = "[{}]".format(",".join(extras))
        if ireq.editable:
            # Make sure that editables don't end up into the cache with
            # a version of a real non-editable package
            extras_string += ':EDITABLE:{}'.format(ireq.link)
        return name, "{}{}".format(version, extras_string)

    def read_cache(self):
        """Reads the cached contents into memory."""
        if os.path.exists(self._cache_file):
            self._cache = read_cache_file(self._cache_file)
        else:
            self._cache = {}

    def write_cache(self):
        """Writes the cache to disk as JSON."""
        doc = {
            '__format__': 1,
            'dependencies': self._strip_unpinned_and_editables(self._cache),
        }
        with open(self._cache_file, 'w') as f:
            json.dump(doc, f, sort_keys=True)

    def clear(self):
        self._cache = {}
        self.write_cache()

    def __contains__(self, ireq):
        pkgname, pkgversion_and_extras = self.as_cache_key(ireq)
        return pkgversion_and_extras in self.cache.get(pkgname, {})

    def __getitem__(self, ireq):
        pkgname, pkgversion_and_extras = self.as_cache_key(ireq)
        return self.cache[pkgname][pkgversion_and_extras]

    def __setitem__(self, ireq, values):
        pkgname, pkgversion_and_extras = self.as_cache_key(ireq)
        self.cache.setdefault(pkgname, {})
        self.cache[pkgname][pkgversion_and_extras] = values
        self.write_cache()

    def get(self, ireq, default=None):
        pkgname, pkgversion_and_extras = self.as_cache_key(ireq)
        return self.cache.get(pkgname, {}).get(pkgversion_and_extras, default)

    def reverse_dependencies(self, ireqs):
        """
        Returns a lookup table of reverse dependencies for all the given ireqs.

        Since this is all static, it only works if the dependency cache
        contains the complete data, otherwise you end up with a partial view.
        This is typically no problem if you use this function after the entire
        dependency tree is resolved.
        """
        cache_key_names = {
            self.as_cache_key(ireq): name_from_ireq(ireq)
            for ireq in ireqs
        }
        """
        Generate a lookup table of reverse dependencies for all the given
        cache keys.

        Example cache keys:

            [('pep8', '1.5.7'),
             ('flake8', '2.4.0'),
             ('mccabe', '0.3'),
             ('pyflakes', '0.8.1')]

        Example result:

            {'pep8': ['flake8'],
             'flake8': [],
             'mccabe': ['flake8'],
             'pyflakes': ['flake8']}
        """

        # First, collect all the dependencies into a sequence of (parent, child) tuples, like [('flake8', 'pep8'),
        # ('flake8', 'mccabe'), ...]
        return lookup_table(
            (key_from_req(Requirement.parse(dep_name)), req_name)
            for (cache_key, req_name) in cache_key_names.items()
            for dep_name in self.cache[cache_key[0]][cache_key[1]])

    @classmethod
    def _strip_unpinned_and_editables(cls, cache):
        """
        Strip out unpinned and editable deps from given dep cache map.
        """
        stripped = type(cache)()
        for (name, dep_map) in cache.items():
            stripped_dep_map = type(dep_map)()
            for (version, deps) in dep_map.items():
                if ':UNPINNED:' not in version and ':EDITABLE:' not in version:
                    stripped_dep_map[version] = deps
            stripped[name] = stripped_dep_map
        return stripped
