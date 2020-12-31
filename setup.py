# -*- coding: utf-8 -*-
from setuptools import setup

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
   name='pyAA',
   version='0.9',
   description='A powerful tool for managing Archiver Appliance',
   license="MIT",
   long_description=long_description,
   author='Yong Hu',
   author_email='yhu@bnl.gov',
   url="https://gitlab.nsls2.bnl.gov/accelerator/pyAA",
   packages=['pyAA'],  #same as name
   install_requires=['requests', 'pandas'], #external packages as dependencies
)

