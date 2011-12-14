import os
from jenkinsutils import BuildHelper

package = 'BlazeWeb'
type = 'build'

bh = BuildHelper(package, type)

# delete & re-create the venv
bh.venv_create()

## install package w/ setuptools develop
bh.setuppy_develop()

# add our bin directory to PATH for subprocesses
bh.add_bin_to_path()

## run tests
bh.vepycall('nosetests', 'tests', '--with-xunit')
