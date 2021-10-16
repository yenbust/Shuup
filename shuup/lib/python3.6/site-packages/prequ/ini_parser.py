from __future__ import unicode_literals

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

text = type('')

bool_or_auto = 'bool_or_auto'


class ParseError(Exception):
    pass


def parse_ini(fileobj, field_specs, section_name):
    parser = configparser.RawConfigParser()
    readfile = getattr(parser, 'read_file', getattr(parser, 'readfp', None))
    readfile(fileobj)
    if not parser.has_section(section_name):
        return None
    result = {}
    for (key, value) in parser.items(section_name):
        spec = field_specs.get(key, text)
        result[key] = _parse_value(parser, section_name, key, value, spec)
    return result


def _parse_value(parser, section_name, key, value, spec):
    if spec in (bool, bool_or_auto):
        if spec == bool_or_auto and value == 'auto':
            return 'auto'
        try:
            return parser.getboolean(section_name, key)
        except ValueError:
            raise ParseError(
                'Unknown bool value for option "{}": {!r}'.format(key, value))
    elif spec == text:
        return value
    elif isinstance(spec, list):
        if spec == [text]:
            return [x for x in value.splitlines() if x]
    elif isinstance(spec, dict):
        if spec == {text: text}:
            return dict(x.split(' = ', 1) for x in value.splitlines() if x)
    raise NotImplementedError("Type spec not implemented: {!r}".format(spec))
