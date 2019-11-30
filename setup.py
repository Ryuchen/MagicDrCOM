# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


setup(
    name='MagicDrCOM',
    version='1.0.0',
    description=(
        '第三方DrCOM登陆器'
    ),
    long_description=open('README.md', 'rb').read().decode('utf8'),
    author='Ryuchen',
    author_email='chenhaom1993@hotmail.com',
    maintainer='Ryuchen',
    maintainer_email='chenhaom1993@hotmail.com',
    license='GNU General Public License v3 (GPLv3)',
    packages=find_packages(),
    platforms=["all"],
    url='https://github.com/ryuchen/liarcom',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
    install_requires=[
        'PyQt5'
    ]
)

