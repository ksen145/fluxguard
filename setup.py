import os
from setuptools import setup, find_packages

setup(
    name='fluxguard',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'fluxguard': ['*.py', 'adapters/*.py'],
    },
    install_requires=[],
    author='Egor Safonov',
    author_email='ksen10405@gmail.com',
    description='Library for monitoring and adapting asynchronous Python code',
    long_description=open('README.md').read() if os.path.exists('README.md') else '',
    long_description_content_type='text/markdown',
    url='https://github.com/ksen145/fluxguard',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
