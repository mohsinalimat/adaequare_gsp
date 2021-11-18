from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in adaequare_gsp/__init__.py
from adaequare_gsp import __version__ as version

setup(
    name="adaequare_gsp",
    version=version,
    description="API's for India GST, integration with ERPNext",
    author="Resilient Tech",
    author_email="sagar@resilient.tech",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
