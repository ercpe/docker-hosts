#!/usr/bin/env python
# -*- coding: utf-8 -*-

#from distutils.core import setup
from setuptools import setup

setup(
    name='docker_hosts',
    version="0.2",
    author='Johann Schmitz',
    author_email='johann@j-schmitz.net',
    description='Dynamically creates /etc/hosts entries for docker containers',
    license='GPL-3',
    url='https://git.ercpe.de/ercpe/docker-hosts',
    packages=['docker_hosts'],
    entry_points = {
        'console_scripts': ['docker-hosts=docker_hosts.__main__'],
    }
)
