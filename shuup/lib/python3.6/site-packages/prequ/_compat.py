try:
    from contextlib import ExitStack
    from tempfile import TemporaryDirectory
except ImportError:  # pragma: py2 only
    from shutil import rmtree as _rmtree

    from contextlib2 import ExitStack
    import backports.tempfile

    class TemporaryDirectory(backports.tempfile.TemporaryDirectory):
        @classmethod
        def _cleanup(cls, name, warn_message):
            _rmtree(name)


__all__ = ['ExitStack', 'TemporaryDirectory']
