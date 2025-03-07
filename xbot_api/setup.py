"""
XBot API Setup Script
"""

from setuptools import setup, find_packages

setup(
    name="xbot-api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "requests",
        "pillow",
    ],
    author="XBot Team",
    author_email="example@example.com",
    description="REST API for accessing Telegram Bot functionality",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/username/xbot-api",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.8",
)