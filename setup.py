from setuptools import setup, find_packages # type: ignore

setup(
	name='mdl',
	version='0.9.1',
	packages=find_packages(include=['mdl']),
	install_requires=[
		"beautifulsoup4",
		"more-itertools",
		"Pygments",
		"regex",
		"typing-extensions",
	],
)
