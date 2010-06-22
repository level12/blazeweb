import platform
import os
from os import environ
from os import path
import shlex
from shutil import rmtree
from subprocess import check_call
import sys
import tempfile

if 'Windows' == platform.system():
    is_win = True
else:
    is_win = False

venv_name = 'bwcandt-venv'
bpath = path.join(tempfile.gettempdir(), venv_name)
if is_win:
    binpath = path.join(bpath, 'Scripts')
    path_sep = ';'
else:
    binpath = path.join(bpath, 'bin')
    path_sep = ':'
distpath = path.join(bpath, 'src', 'default')
testspath = path.join(distpath, 'tests')

venv = os.environ.copy()
venv['VIRTUAL_ENV'] = bpath
venv['PATH'] = binpath + path_sep + venv['PATH']

def syscmd(cmd, **kwargs):
    check_call(cmd, shell=True, **kwargs)

def venvcmd(cmd, **kwargs):
    check_call(cmd, shell=True, env=venv, **kwargs)

try:
    rmtree(bpath)
except OSError:
    pass
syscmd('virtualenv %s --no-site-packages' % bpath)
syscmd('mkdir ' + path.join(bpath, 'src'))
syscmd('hg clone https://rsyring@bitbucket.org/rsyring/blazeweb ' + distpath)
venvcmd('python setup.py develop', cwd=distpath)
venvcmd('easy_install webtest scripttest')
venvcmd('nosetests --nologcapture', cwd=testspath)
