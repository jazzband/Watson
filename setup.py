#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup file for the Watson distribution."""

from os.path import join

from setuptools import setup

with open('README.rst') as f:
    readme = f.read()

# read package meta-data from version.py
pkg = {}
mod = join('watson', 'version.py')
exec(compile(open(mod).read(), mod, 'exec'), {}, pkg)


def parse_requirements(requirements, ignore=('setuptools',)):
    """Read dependencies from requirements file (with version numbers if any)

    Note: this implementation does not support requirements files with extra
    requirements
    """
    with open(requirements) as f:
        packages = set()
        for line in f:
            line = line.strip()
            if line.startswith(('#', '-r', '--')):
                continue
            if '#egg=' in line:
                line = line.split('#egg=')[1]
            pkg = line.strip()
            if pkg not in ignore:
                packages.add(pkg)
        return tuple(packages)


setup(
    name='td-watson',
    version=pkg['version'],
    description='A wonderful CLI to track your time!',
    packages=['watson'],
    author='TailorDev',
    author_email='contact@tailordev.fr',
    license='MIT',
    long_description=readme,
    install_requires=parse_requirements('requirements.txt'),
    tests_require=parse_requirements('requirements-dev.txt'),
    entry_points={
        'console_scripts': [
            'watson = watson.__main__:cli',
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Customer Service",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    keywords='watson time-tracking time tracking monitoring report',
)
