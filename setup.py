"""
Introduction
---------------

pysmvt is a wsgi web framework library designed in the spirit of Pylons but with
Django modularity (i.e. what they would call "apps").  If you want to try it out
it would be best to start with
`our example application <http://pypi.python.org/pypi/PysAppExample/>`_.

Steps for Installation
----------------------

#. Install Python
#. install setuptools (includes easy_install)
#. install virtualenv `easy_install virtualenv`
#. Create a new virtual environement `virtualenv myproj-staging --no-site-packages`
#. `Activate the virtual environment (os dependent) <http://pypi.python.org/pypi/virtualenv#activate-script>`_
#. install pysmvt & dependencies `easy_install pysmvt`

Steps for creating a working application
-----------------------------------------
#. `cd myproj-staging`
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

The code for 0.1 is pretty stable.  API, however, will be changing in 0.2.

The unstable `development version
<https://svn.rcslocal.com:8443/svn/pysmvt/pysmvt/trunk#egg=pysmvt-dev>`_.
"""
import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name = "pysmvt",
    version = "0.1.1",
    description = "A wsgi web framework with a pylons spirit and django modularity",
    long_description = __doc__,
    author = "Randy Syring",
    author_email = "randy@rcs-comp.com",
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
        "Beaker>=1.1.3",
        "decorator>=3.0.1",
        "FormEncode>=1.2.2",
        "html2text>=2.35",
        "jinja2>=2.1.1",
        "markdown2>=1.0.1.11",
        "nose>=0.10.4",
        "Paste>=1.7.2",
        "PasteScript>=1.7.3",
        "pysutils>=0.1",
        "Werkzeug>=0.5"
    ],
    entry_points="""
    [console_scripts]
    pysmvt = pysmvt.script:main
    
    [pysmvt.pysmvt_project_template]
    pysmvt = pysmvt.paster_tpl:ProjectTemplate
    
    [pysmvt.pysmvt_module_template]
    pysmvt = pysmvt.paster_tpl:ModuleTemplate
    
    [nose.plugins]
    pysmvt_testsfrompackage = pysmvt.test:TestsFromPackagePlugin
    pysmvt_initcurrentapp = pysmvt.test:InitCurrentAppPlugin
    """,
    zip_safe=False
)