"""
	Test driver for document tests.
"""
import os
from mdl import tree_parser
from shelljob import fs

def passed(text : str) -> str:
	return '\x1b[32m{} ✔ \x1b[m'.format(text)

def failed(text : str) -> str:
	return '\x1b[31m{} ✗\x1b[m'.format(text)

def status(text, okay):
	print( passed(text) if okay else failed(text), end=' ' )
	
for fname in fs.find( 'test/docs', name_regex = r".*\.mdl" ):
	print( fname, end= ' ' )
	parsed = tree_parser.parse_file( fname )
	base = os.path.splitext( fname )[0]
	
	parse_name = base + '.parse'
	if os.path.exists( parse_name ):
		parse_dump = tree_parser.get_dump( parsed )
		with open( parse_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
		
		status( 'Parse', parse_dump == check_dump )
	print()
		
		
		
