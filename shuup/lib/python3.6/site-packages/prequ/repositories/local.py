# coding: utf-8
from __future__ import (
    absolute_import, division, print_function, unicode_literals)

from ..utils import (
    as_tuple, check_is_hashable, key_from_ireq, make_install_requirement)
from .base import BaseRepository


def ireq_satisfied_by_existing_pin(ireq, existing_pin):
    """
    Return True if the given InstallationRequirement is satisfied by the
    previously encountered version pin.
    """
    version = next(iter(existing_pin.req.specifier)).version
    return version in ireq.req.specifier


class LocalRequirementsRepository(BaseRepository):
    """
    The LocalRequirementsRepository proxied the _real_ repository by first
    checking if a requirement can be satisfied by existing pins (i.e. the
    result of a previous compile step).

    In effect, if a requirement can be satisfied with a version pinned in the
    requirements file, we prefer that version over the best match found in
    PyPI.  This keeps updates to the requirements.txt down to a minimum.
    """
    def __init__(self, existing_pins, proxied_repository):
        self.repository = proxied_repository
        self.existing_pins = existing_pins

    @property
    def finder(self):
        return self.repository.finder

    @property
    def session(self):
        return self.repository.session

    @property
    def DEFAULT_INDEX_URL(self):  # noqa (N802)
        return self.repository.DEFAULT_INDEX_URL

    def clear_caches(self):
        self.repository.clear_caches()

    def freshen_build_caches(self):
        self.repository.freshen_build_caches()

    def find_best_match(self, ireq, prereleases=None):
        key = key_from_ireq(ireq)
        existing_pin = self.existing_pins.get(key)
        if existing_pin and ireq_satisfied_by_existing_pin(ireq, existing_pin):
            version = as_tuple(existing_pin)[1]
            return make_install_requirement(
                existing_pin.name, version,
                ireq.extras, constraint=ireq.constraint)
        else:
            return self.repository.find_best_match(ireq, prereleases)

    def _get_dependencies(self, ireq):
        return self.repository._get_dependencies(ireq)

    def get_hashes(self, ireq):
        check_is_hashable(ireq)
        pinned_ireq = self.existing_pins.get(key_from_ireq(ireq))
        if pinned_ireq and ireq_satisfied_by_existing_pin(ireq, pinned_ireq):
            if pinned_ireq.has_hash_options:
                return set(_get_hashes_from_ireq(pinned_ireq))
        return self.repository.get_hashes(ireq)


def _get_hashes_from_ireq(ireq):
    """
    :type ireq: pip.req.InstallRequirement
    """
    hashes = ireq.hashes()
    for (alg, hash_values) in hashes._allowed.items():
        for hash_value in hash_values:
            yield '{}:{}'.format(alg, hash_value)
