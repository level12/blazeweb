"""
Portions of this module were taken from shutil.py in the Python 2.6.5 standard
library.

- modified copytree() to work when the directory exists

"""

import os
from os import path
from shutil import copy2, copystat, rmtree

from blazeutils import NotGiven

from blazeweb.globals import settings
from blazeweb.hierarchy import list_component_mappings, hm

__all__ = [
    'mkdirs',
    'copy_static_files',
]

class Error(EnvironmentError):
    pass

try:
    WindowsError
except NameError:
    WindowsError = None

def mkdirs(newdir, mode=NotGiven):
    """
        a "safe" verision of makedirs() that will only create the directory
        if it doesn't already exist.  This avoids having to catch an Error
        Exception that might be a result of the directory already existing
        or might be a result of an error creating the directory.  By checking
        for the diretory first, any exception was created by the directory
        not being able to be created.
    """
    if mode is NotGiven:
        mode = settings.default.dir_mode
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        os.makedirs(newdir, mode)

def copy_static_files(delete_existing=False):
    """
        copy's files from the apps and components to the static directory
        defined in the settings.  Files are copied in a hierarchical way
        such that apps and components lower in priority have their files
        overwritten by apps/components with higher priority.
    """
    statroot = settings.dirs.static

    if delete_existing:
        app_stat_path = path.join(statroot, 'app')
        if path.exists(app_stat_path):
            rmtree(app_stat_path)
        component_stat_path = path.join(statroot, 'component')
        if path.exists(component_stat_path):
            rmtree(component_stat_path)

    for app, pname, package in list_component_mappings(reverse=True, inc_apps=True):

        package_mod = hm.builtin_import(package or app, fromlist=[''])
        pkgdir = path.dirname(package_mod.__file__)
        if package or not pname:
            srcpath = pkgdir
        else:
            srcpath = path.join(pkgdir, 'components', pname)
        srcpath = path.join(srcpath, 'static')
        if path.isdir(srcpath):
            if not pname:
                targetpath = 'app'
            else:
                targetpath = path.join('component', pname)
            targetpath = path.join(statroot, targetpath)

            copytree(srcpath, targetpath)

def copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    mkdirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                copy2(srcname, dstname)
            # XXX What about devices, sockets etc.?
        except (IOError, os.error), why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error, err:
            errors.extend(err.args[0])
    try:
        copystat(src, dst)
    except OSError, why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error, errors
