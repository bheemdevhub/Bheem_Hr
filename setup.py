from setuptools import setup, find_packages

setup(
    name='bheem-hr',
    version='1.0.0',
    packages=find_packages(include=["hr", "hr.*"]),
    install_requires=[],
    include_package_data=True,
    description='Bheem Hr ERP module',
    author='Bheem Core Team',
    url='https://github.com/bheemverse/Bheem_Hr'
)
