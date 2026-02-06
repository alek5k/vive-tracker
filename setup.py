from setuptools import setup, find_packages

# This setup.py is kept for backward compatibility
# Modern packaging configuration is in pyproject.toml
setup(
    packages=find_packages(),
    include_package_data=True,
)
