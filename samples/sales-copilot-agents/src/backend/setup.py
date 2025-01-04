from setuptools import setup, find_packages

setup(
    name="api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "azure-ai-projects",
        "azure-ai-evaluation",
        "python-multipart",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
    ],
)