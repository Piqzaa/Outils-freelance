#!/usr/bin/env python3
"""Setup script pour Freelance Manager."""

from setuptools import setup, find_packages

setup(
    name='freelance-manager',
    version='1.0.0',
    description='CLI de gestion devis, factures et contrats pour freelances en France',
    author='Freelance',
    python_requires='>=3.10',
    py_modules=['cli', 'database'],
    packages=['generators'],
    install_requires=[
        'click>=8.1.0',
        'reportlab>=4.0.0',
        'python-docx>=1.0.0',
        'PyYAML>=6.0',
        'Jinja2>=3.1.0',
        'tabulate>=0.9.0',
        'openpyxl>=3.1.0',
    ],
    entry_points={
        'console_scripts': [
            'freelance=cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['config.yaml'],
    },
)
