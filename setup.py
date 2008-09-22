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
        "Werkzeug==0.3.1",
        "SQLAlchemy==0.4.6",
        "Jinja2>=2.0",
        "Elixir==0.5.2",
        "FormAlchemy"
        ]
)