"""
Setup script for Plymouth Bike Station Logger.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="plymouth-bike-logger",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A bike station availability tracker for Plymouth",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/plymouth-bike-logger",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "analytics": ["pandas>=2.0.0", "matplotlib>=3.7.0", "seaborn>=0.12.0"],
        "dev": ["pytest>=7.0.0", "black>=23.0.0", "flake8>=6.0.0"],
    },
    entry_points={
        "console_scripts": [
            "bike-logger-once=scripts.run_once:main",
            "bike-logger-continuous=scripts.run_continuous:main",
            "bike-logger-report=scripts.generate_report:main",
        ],
    },
)