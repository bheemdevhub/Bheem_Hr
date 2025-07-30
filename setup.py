from setuptools import setup, find_packages

setup(
    name="bheem_hr",
    version="1.0.0",
    description="Bheem ERP - HR Module",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    install_requires=[],
)

