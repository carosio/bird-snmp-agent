#!/usr/bin/env python

from distutils.core     import setup

setup(
	name="bird-snmp",
	version="0.2",
	description="BGP4-MIB AgentX support for Bird",
	author="Lex van Roon",
	author_email="r3boot@r3blog.nl",
	url="http://r3blog.nl",
	packages=["bird"],
	scripts=["scripts/bird-agentx"],
	data_files=[
		("/usr/local/share/bird-snmp", ["data/BGP4-MIB.txt"]),
	]
)
