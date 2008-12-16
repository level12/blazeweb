"""
Introduction
---------------

pysmvt is a wsgi web framework library designed in the spirit of pylons but with
django modularity (i.e. what they would call "apps").  If you want to try it out
it would be best to start with `pysapp <http://pypi.python.org/pypi/pysapp/>`_
which is a pysmvt "supporting application" that your projects can be built on.

Current Status
---------------

We are currently in an alpha phase which means lots of stuff can change, maybe rapidly, and we are not interested in backwards compatibility at this point.

I am currently using this library for some production websites, but I wouldn't recommend you do that unless you **really** know what you are doing.

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
    version = "0.1dev",
    description = "A wsgi web framework with a pylons spirit and django modularity",
    long_description = __doc__,
    author = "Randy Syring",
    author_email = "randy@rcs-comp.com",
    url='http://pypi.python.org/pypi/pysmvt/',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
      ],
    license='BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    install_requires = [
        "Beaker>=1.1.2",
        "FormEncode>=1.2",
        "html2text>=1.2",
        "jinja2>=2.1",
        "markdown2>=1.0.1.11",
        "Paste>=1.7.2",
        "PasteScript>=1.7.3",
        "pysutils>=dev",
        "Werkzeug>=0.4"
    ],
    dependency_links = [
        "http://www.aaronsw.com/2002/html2text/html2text.py#egg=html2text-2.3",
        "https://svn.rcslocal.com:8443/svn/pysmvt/pysutils/trunk/#egg=pysutils-dev"
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