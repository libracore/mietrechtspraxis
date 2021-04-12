# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in mietrechtspraxis/__init__.py
from mietrechtspraxis import __version__ as version

setup(
	name='mietrechtspraxis',
	version=version,
	description='All about mietrechtspraxis',
	author='libracore AG',
	author_email='info@libracore.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
