#!/usr/bin/env python
"""The setup script."""

from setuptools import setup, find_packages
import signe


with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

requirements = ["typing_extensions"]

test_requirements = ["pytest>=3"]

setup(
    author="carson_jia",
    author_email="568166495@qq.com",
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ],
    description="...",
    entry_points={
        # 'console_scripts': [
        #     'test_prj=test_prj.cli:main',
        # ],
    },
    install_requires=requirements,
    license="MIT license",
    # long_description=readme,
    include_package_data=True,
    keywords=["signal", "signe", "S.js"],
    name="signe",
    packages=find_packages(include=["signe", "signe.*"]),
    data_files=[],
    test_suite="__tests",
    tests_require=test_requirements,
    url="",
    version=signe.__version__,
    zip_safe=False,
)
