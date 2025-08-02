from setuptools import setup, find_packages

setup(
    name="bheem-hr",
    version="1.0.0",
    packages=find_packages(include=["app*"]),
    include_package_data=True,
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn[standard]>=0.22.0",
        "sqlalchemy>=2.0.0",
        "pydantic>=2.0.0",
        # Add others your module needs
    ],
)