#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    
setup (
    name = "PySMVT",
    version = "0.1",
    packages = find_packages(exclude=["ez_setup"]),
    install_requires = [
        'Beaker==1.0.1',
        'FormEncode==1.0.1',
        "Werkzeug==0.3.1",
        "SQLAlchemy==0.5.0rc1"
        ]
)