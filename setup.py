#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='docker-hosts',
    version="0.1",
    description='Dynamically creates /etc/hosts entries for docker containers',
    author='Johann Schmitz',
    author_email='johann@j-schmitz.net',
    url='https://git.ercpe.de/ercpe/docker-hosts',
    download_url='https://git.ercpe.de/ercpe/docker-hosts',
    packages=find_packages(exclude=('tests', )),
    include_package_data=True,
    zip_safe=False,
    data_file=[("", "LICENSE.txt")],
    license='GPL-3',
)
