"""
Code to allow this package to be pip-installed
"""

import os
import sys

from setuptools import setup
from setuptools import find_packages


LIBRARY_VERSION = "0.0.2"
LEAF_COMMON_VERSION = "1.1.50"

CURRENT_PYTHON = sys.version_info[:2]
REQUIRED_PYTHON = (3, 8)

if CURRENT_PYTHON < REQUIRED_PYTHON:
    sys.stderr.write(f"""
==========================
Unsupported Python version
==========================
This version of leaf-server-common requires Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}, but you're trying to
install it on Python {CURRENT_PYTHON[0]}.{CURRENT_PYTHON[1]}.
""")
    sys.exit(1)


def read(fname):
    """
    Read file contents into a string
    :param fname: File to be read
    :return: String containing contents of file
    """
    with open(os.path.join(os.path.dirname(__file__), fname), encoding="utf-8") as file:
        return file.read()


# Note: we use a direct URL for leaf-common rather than dependency-links, because the pip team has deprecated
# the latter. See: https://github.com/pypa/pip/issues/4187#issuecomment-415067034
setup(
    name='leaf-server-common',
    version=LIBRARY_VERSION,
    python_requires=f'>={REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}',
    packages=find_packages('.', exclude=['tests*', 'build_scripts*']),
    install_requires=[
        # GitHib dependencies have issues with using tokens as source credentials
        # so we do not include them here. Client code just as to know (sorry).
        # At least acknowledge that we have a source-available dependency

        # f"leaf-common @ git+https://github.com/leaf-ai/leaf-common.git@{LEAF_COMMON_VERSION}#egg=leaf-common",
        "grpcio==1.46.3",
        "grpcio-health-checking==1.46.3",
        "grpcio-reflection==1.46.3",
        "grpcio-tools==1.46.3",
        "protobuf==3.19.5",
        "libhoney==2.0.0"
    ],
    description='Library for common service infrastructure for use by LEAF services',
    long_description=read('README.md'),
    author='Dan Fink',
    url='https://github.com/leaf-ai/leaf-server-common/'
)
