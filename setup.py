# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
import os
from setuptools import setup, find_packages

from psychrochart import __version__ as version


packages = find_packages(exclude=['docs', '*tests*', 'notebooks', 'htmlcov'])

basedir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(basedir, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='psychrochart',
    version=version,
    description='A Python 3 library to make psychrometric charts and overlay '
                'information on them.',
    long_description='\n' + long_description,
    keywords='psychrometrics, moist, humid air, climate control, matplotlib',
    author='Eugenio Panadero',
    author_email='eugenio.panadero@gmail.com',
    url='https://github.com/azogue/psychrochart',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=packages,
    package_data={
        'psychrochart': ['chart_styles/*.json'],
    },
    install_requires=['matplotlib>=2.0.2', 'scipy'],
    tests_require=['pytest>=3.0.0', 'pytest-cov'],
)
