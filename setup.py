"""
Setup script for NLQ Translator.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="nlq_translator",
    version="0.1.0",
    author="NLQ Translator Team",
    author_email="info@nlq-translator.com",
    description="A library for translating natural language to database queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nlq-translator/nlq-translator",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "elasticsearch>=8.0.0",
        "pyyaml>=6.0",
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
        ],
        "web": [
            "flask>=2.0.0",
            "flask-cors>=3.0.0",
            "gunicorn>=20.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nlq-translator=nlq_translator.cli:main",
        ],
    },
)
