#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import sys

install_requirements = []

if sys.version_info[0] == 2:
    install_requirements = [
        'enum34==1.1.6',
        'futures==3.2.0',
        'grpcio==1.10.0',
        'grpcio-tools==1.10.0',
        'protobuf==3.5.2',
        'six==1.11.0',
    ]
elif sys.version_info[0] == 3:
    install_requirements = [
        'grpcio==1.10.0',
        'grpcio-tools==1.10.0',
        'protobuf==3.5.2',
        'six == 1.11.0',
    ]
else:
    raise Exception("unknow python version.")

setup(
    name='PythonGRPCKit',
    version='0.0.3',
    url='https://github.com/htwenning/python_kit',
    license='BSD',
    author='wenning',
    author_email='ht.wenning@foxmail.com',
    description='Write grpc application like Flask.',
    packages=['python_kit'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=install_requirements,
)
