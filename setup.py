# -*- coding: utf-8 -*-
"""
A python library to make psychrometric charts and overlay information in them.

"""
from setuptools import setup, find_packages
from psychrochart import __version__ as version


packages = find_packages(exclude=['docs', '*tests*', 'notebooks', 'htmlcov'])

setup(
    name='psychrochart',
    version=version,
    description='A Python 3 library to make psychrometric charts and overlay '
                'information on them.',
    keywords='psychrometrics, moist, humid air, climate control, matplotlib',
    author='Eugenio Panadero',
    author_email='eugenio.panadero@gmail.com',
    url='https://github.com/azogue/psychrochart',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Physics',
        'Topic :: Scientific/Engineering :: Visualization',
        'License :: OSI Approved :: MIT License',
        # 'Natural Language :: Spanish',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
    packages=packages,
    package_data={
        'psychrochart': ['*.json'],
    },
    install_requires=['numpy', 'matplotlib'],
    tests_require=['pytest>=3.0.0'],
)
