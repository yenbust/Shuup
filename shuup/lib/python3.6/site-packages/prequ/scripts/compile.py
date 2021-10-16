import difflib
import os
from tempfile import NamedTemporaryFile

import click

from . import compile_in
from ..configuration import PrequConfiguration
from ..exceptions import FileOutdated, PrequError
from ..logging import log

click.disable_unicode_literals_warning = True


@click.command()
@click.option('-v', '--verbose', is_flag=True, help="Show more output")
@click.option('-s', '--silent', is_flag=True, help="Show no output")
@click.option('-c', '--check', is_flag=True,
              help="Check if the generated files are up-to-date")
@click.pass_context
def main(ctx, verbose, silent, check):
    """
    Compile requirements from source requirements.
    """
    try:
        compile(ctx, verbose, silent, check)
    except PrequError as error:
        if not check or not silent:
            log.error('{}'.format(error))
        raise SystemExit(1)


def compile(ctx, verbose, silent, check):
    info = log.info if not silent else (lambda x: None)
    conf_cls = PrequConfiguration if not check else CheckerPrequConfiguration
    conf = conf_cls.from_directory('.')

    compile_opts = dict(conf.get_prequ_compile_options())
    compile_opts.update(verbose=verbose, silent=(not verbose))
    if check:
        compile_opts.update(verbose=False, silent=True)

    try:
        for label in conf.labels:
            if not check:
                info('*** Compiling {}'.format(
                    conf.get_output_file_for(label)))
            do_one_file(ctx, conf, label, compile_opts)
            if isinstance(conf, CheckerPrequConfiguration):
                conf.check(label, info, verbose)
    finally:
        if isinstance(conf, CheckerPrequConfiguration):
            conf.cleanup()


def do_one_file(ctx, conf, label, compile_opts):
    out_file = conf.get_output_file_for(label)
    content = conf.get_requirements_in_for(label).encode('utf-8')
    with get_tmp_file(prefix=out_file, suffix='.in') as tmp:
        tmp.write(content)
    try:
        ctx.invoke(compile_in.cli, src_files=[tmp.name], output_file=out_file,
                   **compile_opts)
    finally:
        os.remove(tmp.name)


class CheckerPrequConfiguration(PrequConfiguration):
    def __init__(self, *args, **kwargs):
        super(CheckerPrequConfiguration, self).__init__(*args, **kwargs)
        self.tmp_out_files = {}

    def get_output_file_for(self, label):
        real_output_file = (
            super(CheckerPrequConfiguration, self).get_output_file_for(label))
        try:
            return self.tmp_out_files[label]
        except KeyError:
            self._check_exists(real_output_file)
            with get_tmp_file(prefix='req-' + label, suffix='.txt') as tmp:
                filename = tmp.name
                tmp.write(_read_file(real_output_file))
            self.tmp_out_files[label] = filename
            return filename

    @classmethod
    def _check_exists(cls, filename):
        if not os.path.exists(filename):
            raise FileOutdated('{} is missing'.format(filename))

    def check(self, label, info, verbose=False):
        cur = super(CheckerPrequConfiguration, self).get_output_file_for(label)
        new = self.get_output_file_for(label)
        if files_have_same_content(cur, new):
            info('{} is OK'.format(cur))
        else:
            if verbose:
                cur_lines = _read_file(cur).decode('utf-8').splitlines()
                new_lines = _read_file(new).decode('utf-8').splitlines()
                diff = difflib.unified_diff(
                    cur_lines, new_lines,
                    cur + ' (current)', cur + ' (expected)')
                for line in diff:
                    info(line.rstrip('\n'))
            raise FileOutdated('{} is outdated'.format(cur))

    def cleanup(self):
        for filename in self.tmp_out_files.values():
            os.remove(filename)


def get_tmp_file(prefix, suffix):
    return NamedTemporaryFile(
        dir='.', prefix=prefix, suffix=suffix, delete=False)


def files_have_same_content(filepath1, filepath2):
    return _read_file(filepath1) == _read_file(filepath2)


def _read_file(path):
    with open(path, 'rb') as fp:
        return fp.read()
