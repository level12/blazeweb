import os
from os import environ
from os import path
import shlex
from shutil import rmtree
from subprocess import check_call
import sys
import tempfile

venv_name = 'bwcandt-venv'
bpath = path.join(tempfile.gettempdir(), venv_name)
binpath = path.join(bpath, 'bin')
distpath = path.join(bpath, 'src', 'default')
testspath = path.join(distpath, 'tests')

venv = os.environ.copy()
venv['VIRTUAL_ENV'] = bpath
venv['PATH'] = "%s:%s" % (binpath, venv['PATH'])

def syscmd(cmd, **kwargs):
    check_call(cmd, shell=True, **kwargs)

def venvcmd(cmd, **kwargs):
    cmd = path.join(binpath, cmd)
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
