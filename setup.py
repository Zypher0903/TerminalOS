from setuptools import setup, find_packages

setup(
    name="TerminalOS",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt6",
        "requests",
        "pyfiglet"
    ],
    entry_points={
        "console_scripts": [
            "terminalos=main:main",
        ],
    },
    author="Your Name",
    author_email="edintahiri.2013@gmail.com",
    description="TerminalOS - A Python-based terminal application",
    url="https://github.com/Zypher0903/TerminalOS",
)
