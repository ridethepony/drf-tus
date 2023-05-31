#!/usr/bin/env python
import os
import re
import sys

from pathlib import Path
from setuptools import setup

REPO_DIR = Path(__file__).parent


def get_version(file_path):
    """Retrieves the version from file_path within this repo"""
    filename = REPO_DIR / file_path
    version_file = filename.read_text()
    version_match = re.search(r'^__version__ = "([^"]+)"', version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


version = get_version("rest_framework_tus/__init__.py")

if sys.argv[-1] == "publish":
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print("Wheel library missing. Please run `pip install wheel`")
        sys.exit()
    os.system("python setup.py sdist upload")
    os.system("python setup.py bdist_wheel upload")
    sys.exit()

if sys.argv[-1] == "tag":
    print("Tagging the version on git:")
    os.system(f"git tag -a {version} -m 'version {version}'")
    os.system("git push --tags")
    sys.exit()

readme = (REPO_DIR / "README.md").read_text()
history = (REPO_DIR / "HISTORY.md").read_text()

setup(
    name="leukeleu-drf-tus",
    version=version,
    description="""A Tus (tus.io) library for Django Rest Framework""",
    long_description=f"{readme}\n{history}",
    long_description_content_type = "text/markdown",
    author="Leukeleu",
    author_email="info@leukeleu.nl",
    url="https://github.com/leukeleu/leukeleu-drf-tus",
    packages=[
        "rest_framework_tus",
    ],
    include_package_data=True,
    install_requires=[
        "Django>=3.2.1",
        "djangorestframework>=3.11.0",
        "jsonfield>=2.0.0",
        "django-fsm==2.7.1"
    ],
    license="MIT",
    zip_safe=False,
    keywords="drf-tus",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.2",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
