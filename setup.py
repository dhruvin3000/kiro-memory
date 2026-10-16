from setuptools import setup, find_packages

setup(
    name="kiro-recall",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.35.0",
        "python-dotenv>=1.0.1",
        "gitpython>=3.1.43",
        "click>=8.1.7",
        "rich>=13.7.1",
        "pydantic>=2.7.4",
        "tinydb>=4.8.0",
        "fastapi>=0.111.0",
        "uvicorn>=0.30.1",
    ],
    extras_require={
        "semantic": [
            "chromadb>=0.5.3",
            "sentence-transformers>=3.0.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "kiro-recall=src.cli.main:main",
        ],
    },
    python_requires=">=3.10",
)
