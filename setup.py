from setuptools import setup, find_packages

setup(
    name="deep-lynx-integration",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.88.0",
        "uvicorn==0.20.0",
        "deep-lynx>=0.1.7",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dotenv>=1.0.0",
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "requests>=2.31.0",
        "urllib3>=2.0.0",
        "python-jose[cryptography]>=3.3.0",
        "python-multipart>=0.0.5",
        "aiosqlite>=0.17.0",
        "tortoise-orm>=0.19.2"
    ],
    python_requires=">=3.12",
) 