import os
import re

from setuptools import find_packages, setup


def get_version(filename):
    with open(filename, "r") as fp:
        contents = fp.read()
    return re.search(r"__version__ = ['\"]([^'\"]+)['\"]", contents).group(1)


version = get_version(os.path.join("patchy", "__init__.py"))

with open("README.rst", "r") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst", "r") as history_file:
    history = history_file.read().replace(".. :changelog:", "")


setup(
    name="patchy",
    version=version,
    description="Patch the inner source of python functions at runtime.",
    long_description=readme + "\n\n" + history,
    author="Adam Johnson",
    author_email="me@adamj.eu",
    url="https://github.com/adamchainz/patchy",
    project_urls={
        "Changelog": "https://github.com/adamchainz/patchy/blob/master/HISTORY.rst"
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    install_requires=[],
    python_requires=">=3.5.*",
    license="BSD",
    zip_safe=False,
    keywords="patchy",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
