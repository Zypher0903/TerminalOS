from setuptools import setup,

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
			"terminalos=core.terminal:main",
		],
	},
	author="Edin",
	author_email="edintahiri.2013@gmail.com"
	description="TerminalOS - python app"
	url="https://github.com/Zypher0903/TerminalOS",
)
