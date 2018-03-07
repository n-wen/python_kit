#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name='PythonKit',
    version='0.0.1',
    url='https://github.com/htwenning/python_kit',
    license='BSD',
    author='wenning',
    author_email='ht.wenning@foxmail.com',
    description='Write grpc application like Flask.',
    packages=['python_kit'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'backports-abc',
        'certifi',
        'contextlib2',
        'enum34',
        'future',
        'futures',
        'grpcio>=1.10.0',
        'grpcio-tools>=1.10.0',
        'jaeger-client>=3.7.1',
        'opentracing>=1.3.0',
        'opentracing-instrumentation>=2.4.0',
        'protobuf>=3.5.1',
        'singledispatch>=3.4.0.3',
        'six>=1.11.0',
        'threadloop>=1.0.2',
        'thrift>=0.11.0',
        'tornado>=4.5.3',
        'wrapt>=1.10.11'
    ],
)