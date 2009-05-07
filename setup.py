"""
Introduction
---------------

pysmvt is a wsgi web framework library designed in the spirit of Pylons but with
Django modularity (i.e. what they would call "apps").  If you want to try it out
it would be best to start with
`our example application <http://pypi.python.org/pypi/PysAppExample/>`_.

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
    version = "0.1",
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

    """,
    zip_safe=False
)