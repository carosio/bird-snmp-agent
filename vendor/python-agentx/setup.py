#!/usr/bin/env python
from distutils.core import setup, Extension
try:
	import ctypes
except:
	print('This agentx module requires a ctypes module in order to work')
	import sys
	sys.exit(1)

setup(
	name			= 'agentx',
	version			= '0.8',
	description		= 'Python 2.x and 3.x module for SNMP AgentX functionality',
	long_description	= 'This is a Python 2.x and 3.x module that enables SNMP AgentX functionality',
	author			= 'Bozhin Zafirov',
	author_email		= 'bozhin@abv.bg',
	py_modules		= ['agentx'],
	license			= 'GPL 3',
)
