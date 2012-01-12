import os
import sys
try:
    from setuptools import setup, find_packages
    from setuptools.command.develop import develop as STDevelopCmd
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

class DevelopCmd(STDevelopCmd):
    def run(self):
        # add in requirements for testing only when using the develop command
        self.distribution.install_requires.extend([
            'WebTest',
            'ScriptTest',
            'docutils',
        ])
        STDevelopCmd.run(self)

cdir = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(cdir, 'readme.rst')).read()
CHANGELOG = open(os.path.join(cdir, 'changelog.rst')).read()

import blazeweb
version = blazeweb.VERSION

required_packages = [
    'Beaker>=1.5',
    # need the .rst stuff, once BlazeUtils makes a release, this can be changed
    'BlazeUtils ==dev, >0.3.7',
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
    name = "BlazeWeb",
    version = version,
    description = "A light weight WSGI framework with a pluggable architecture",
    long_description= '\n\n'.join((README, CHANGELOG)),
    author = "Randy Syring",
    author_email = "rsyring@gmail.com",
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
    install_requires = required_packages,
    cmdclass = {'develop': DevelopCmd},
    tests_require=['webtest', 'scripttest'],
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
    """,
    zip_safe=False
)
