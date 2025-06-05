from setuptools import setup, find_packages

setup(
    name="atm_interface",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "supabase",
        "pytest",
        "pytest-asyncio",
        "email-validator"
    ],
) 