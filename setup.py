import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

setup(
    name = "pysmvt",
    version = "0.1.0",
    description = "A wsgi compliant web framework",
    author = "Randy Syring",
    author_email = "randy@rcs-comp.com",
    url='http://pypi.python.org/pypi/pysmvt',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
      ],
    license='BSD',
    packages=['pysmvt'],
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

    """,
    zip_safe=False
)