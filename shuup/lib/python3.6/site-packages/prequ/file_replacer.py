import errno
import os
import shutil
import sys
from tempfile import NamedTemporaryFile

text_type = type(u'')


class FileReplacer(object):
    """
    Create or replace a file in filesystem atomically.

    Acts as a context manager.  Entering the context returns a file
    handle to a writable (hidden) temporary file holding the contents
    until moving the temporary file to the destination path on succesful
    close (at context manager exit).  Any existing file at the
    destination path will be replaced.

    Contents of the temporary file will be discarded, if any exception
    is raised while in the context.
    """
    tmpfile = None

    def __init__(self, dest_path):
        self.dest_path = dest_path
        self.tmpfile = NamedTemporaryFile(
            dir=os.path.dirname(dest_path),
            prefix=('.' + os.path.basename(dest_path) + '-'),
            delete=False)

    def __enter__(self):
        return self.tmpfile.__enter__()

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        result = self.tmpfile.__exit__(exc_type, exc_val, exc_tb)
        self.close(do_replace=(exc_type is None))
        return result

    def __del__(self):
        self.close(do_replace=False)

    def close(self, do_replace=True):
        replaced = False
        if self.tmpfile:
            tmppath = self.tmpfile.name
            try:
                self.tmpfile.close()
                self.tmpfile = None
                if do_replace:
                    replace(tmppath, self.dest_path)
                    replaced = True
            finally:
                if not replaced:
                    os.unlink(tmppath)
        return replaced


class _NeverRaisedException(Exception):
    """Dummy exception that shouldn't ever be raised."""


try:
    rename_exception_to_handle = WindowsError
except NameError:  # pragma: non-windows only
    rename_exception_to_handle = _NeverRaisedException


def replace(src, dst):
    """
    Replace a file with another.

    :type src: str
    :param src: Source file path
    :type dst: str
    :param dst: Destination path, the file to replace
    """
    # Set the permissions of src by copying them from dst
    _copy_or_init_permissions(target_file=src, source_file=dst)
    try:
        return os.rename(src, dst)
    except rename_exception_to_handle as error:  # pragma: windows only
        if error.errno != errno.EEXIST:
            raise

        # On Windows we get here if dst file exists.  Use ReplaceFile
        # from Windows API to replace the file atomically.

        import ctypes
        import ctypes.wintypes

        replace_file = ctypes.windll.kernel32.ReplaceFile
        replace_file.argtypes = [
            ctypes.c_wchar_p,  # lpReplacedFileName
            ctypes.c_wchar_p,  # lpReplacementFileName
            ctypes.c_wchar_p,  # lpBackupFileName (optional)
            ctypes.wintypes.DWORD,  # dwReplaceFlags
            ctypes.wintypes.LPVOID,  # lpExclude (reserved)
            ctypes.wintypes.LPVOID,  # lpReserved (reserved)
        ]

        replace_succeeded = replace_file(
            ctypes.c_wchar_p(_path_to_unicode(dst)),
            ctypes.c_wchar_p(_path_to_unicode(src)),
            None, 0, None, None)
        if not replace_succeeded:
            raise OSError("Failed to replace %r with %r" % (dst, src))


def _copy_or_init_permissions(target_file, source_file):
    """
    Set target file permissions from source file or from umask.

    If source file exists, copy its permissions.  Otherwise set default
    permissions using current umask.
    """
    try:
        shutil.copymode(source_file, target_file)
    except OSError:  # src did not exist
        os.chmod(target_file, 0o666 & ~_get_umask())


def _get_umask():
    """
    Get current umask (without changing it as os.umask does).
    """
    umask = os.umask(0)  # Get umask and set it to 0
    os.umask(umask)  # Set umask back to its original value
    return umask


def _path_to_unicode(path):
    """
    Convert filesystem path to unicode.

    >>> if sys.getfilesystemencoding().lower() in ['utf-8', 'utf-16']:
    ...     encoded_path = u'X\u20acY'.encode(sys.getfilesystemencoding())
    ...     assert _path_to_unicode(encoded_path) == u'X\u20acY'

    >>> assert _path_to_unicode(b'some ascii content') == u'some ascii content'
    >>> assert _path_to_unicode(u'some unicode') == u'some unicode'
    >>> assert type(_path_to_unicode(b'x')) == type(u'')
    >>> assert type(_path_to_unicode(u'x')) == type(u'')

    :type path: bytes|unicode
    :rtype: unicode
    """
    if isinstance(path, text_type):
        return path
    encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
    return path.decode(encoding)
