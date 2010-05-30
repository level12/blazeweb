"""
Introduction
---------------

pysmvt is a wsgi web framework library designed in the spirit of Pylons but with
Django modularity (i.e. what they would call "apps").

Steps for Installation
----------------------

#. Install Python
#. install setuptools (includes easy_install)
#. install virtualenv `easy_install virtualenv`
#. Create a new virtual environement `virtualenv pysmvttest-venv --no-site-packages`
#. `Activate the virtual environment (os dependent) <http://pypi.python.org/pypi/virtualenv#activate-script>`_
#. install pysmvt & dependencies `easy_install pysmvt` or `pip install pysmvt`

Steps for creating a working application
-----------------------------------------
#. `cd pysmvttest-venv`
#. `mkdir src`
#. `cd src`
#. `pysmvt project myapp`
#. answer the questions that come up.  Note what you put for
    "Enter author (your name)" as <user>.  If you forget, look in myapp/settings.py.
#. `cd myapp-dist`
#. `python setup.py -q develop`
#.  `nosetests` you should get three succesful tests
#. `cd myapp`
#. `pysmvt serve <user>` run a development http server with the user's settings 
   profile
#. point your browser at http://localhost:5000/
    
Creating a New Application Module
---------------------------------
This step creates a Application Module directory structure in myapp/modules/<mymod>:

`pysmvt module <mymod>`

where <mymod> is the name of the module you want to create

Questions & Comments
---------------------

Please visit: http://groups.google.com/group/pyslibs

Current Status
---------------

The code stays pretty stable, but the API is likely to change in the future.

The `pysmvt tip <http://bitbucket.org/rsyring/pysmvt/get/tip.zip#egg=pysmvt-dev>`_
is installable via `easy_install` with ``easy_install pysmvt==dev``
"""
import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

version = '0.2.1'

setup(
    name = "pysmvt",
    version = version,
    description = "A wsgi web framework with a pylons spirit and django modularity",
    long_description = __doc__,
    author = "Randy Syring",
    author_email = "rsyring@gmail.com",
    url='http://pypi.python.org/pypi/pysmvt/',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
      ],
    license='BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    install_requires = [
        "Beaker>=1.5",
        "decorator>=3.0.1", ## <-- is used?
        "FormEncode>=1.2",
        "html2text>=2.35",
        "jinja2>=2.5",
        "markdown2>=1.0.1",
        "minimock>=1.2",
        "nose>=0.11",
        "Paste>=1.7",
        "PasteScript>=1.7",
        "pysutils>=0.2",
        "simplejson>=2.0", #but only on 2.5, and only if using the json wrapper
        "WebHelpers>=1.0rc1",
        "Werkzeug>=0.6"
    ],
    entry_points="""
    [console_scripts]
    pysmvt = pysmvt.script:main
    
    [pysmvt.pysmvt_project_template]
    pysmvt = pysmvt.paster_tpl:ProjectTemplate
    
    [pysmvt.pysmvt_module_template]
    pysmvt = pysmvt.paster_tpl:ModuleTemplate

    """,
    zip_safe=False
)