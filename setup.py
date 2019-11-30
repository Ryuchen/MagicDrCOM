# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='MagicDrCOM',
    version='1.0.0',
    description='3rd DrCOM client',
    author='ryuchen',
    author_email='chenhaom1993@hotmail.com',
    maintainer='Ryuchen',
    long_description=long_description,
    long_description_content_type="text/markdown",
    maintainer_email='chenhaom1993@hotmail.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/ryuchen/MagicDrCOM',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Natural Language :: Chinese (Simplified)',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3'
    ],
    python_requires='>=3.6',
    install_requires=[
        'PyQt5'
    ]
)

