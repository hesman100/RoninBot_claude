from setuptools import setup, find_packages

setup(
    name="xbot_api",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask",
        "flask-cors",
        "requests",
        "pillow",
    ],
    entry_points={
        "console_scripts": [
            "xbot-api=xbot_api.server:main",
        ],
    },
)