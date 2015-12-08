import os

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

# pip install -e .[develop]
develop_requires = [
    'WebTest',
    'ScriptTest',
    'docutils',
]

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()
CHANGELOG = open(os.path.join(cdir, 'changelog.rst')).read()
VERSION = open(os.path.join(cdir, 'blazeweb', 'version.txt')).read().strip()

required_packages = [
    'Beaker>=1.5',
    'BlazeUtils>0.3.7',
    'Blinker>=1.0',
    'decorator>=3.0.1',
    'FormEncode>=1.2',
    'html2text>=2.35',
    'jinja2>=2.5',
    'markdown2>=1.0.1',
    'minimock',
    'nose>=0.11',
    'Paste>=1.7',
    'PasteScript>=1.7',
    'WebHelpers>=1.0',
    'Werkzeug>=0.6',
]

try:
    import json
    del json
except ImportError:
    required_packages.append('simplejson>=2.1.1')

setup(
    name="BlazeWeb",
    version=VERSION,
    description="A light weight WSGI framework with a pluggable architecture",
    long_description='\n\n'.join((README, CHANGELOG)),
    author="Randy Syring",
    author_email="randy.syring@level12.io",
    url='http://pypi.python.org/pypi/BlazeWeb/',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP'
    ],
    license='BSD',
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    install_requires=required_packages,
    extras_require={'develop': develop_requires},
    entry_points="""
    [console_scripts]
    bw = blazeweb.scripting:blazeweb_entry

    [blazeweb.no_app_command]
    help=paste.script.help:HelpCommand
    project = blazeweb.commands:ProjectCommand
    jinja-convert = blazeweb.commands:JinjaConvertCommand

    [blazeweb.app_command]
    serve = blazeweb.commands:ServeCommand
    help = paste.script.help:HelpCommand
    testrun = blazeweb.commands:TestRunCommand
    tasks = blazeweb.commands:TasksCommand
    shell = blazeweb.commands:ShellCommand
    routes = blazeweb.commands:RoutesCommand
    static-copy = blazeweb.commands:StaticCopyCommand
    component-map = blazeweb.commands:ComponentMapCommand


    [blazeweb.blazeweb_project_template]
    minimal = blazeweb.paster_tpl:MinimalProjectTemplate
    bwproject = blazeweb.paster_tpl:ProjectTemplate

    [nose.plugins]
    blazeweb_initapp = blazeweb.nose_plugin:InitAppPlugin

    [pytest11]
    blazeweb_initapp = blazeweb.pytest_plugin
    """,
    zip_safe=False
)
