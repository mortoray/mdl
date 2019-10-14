"""
	Test driver for document tests.
"""
import os, yaml
from mdl import tree_parser, parse_to_doc, format_html, doc_process
import mdl
from shelljob import fs #type: ignore

def passed(text : str) -> str:
	return '\x1b[32m{} ✔ \x1b[m'.format(text)

def failed(text : str) -> str:
	return '\x1b[31m{} ✗\x1b[m'.format(text)

def status(text, okay):
	print( passed(text) if okay else failed(text), end=' ' )
	
for fname in fs.find( 'test/docs', name_regex = r".*\.mdl" ):
	print( fname, end= ' ' )
	base = os.path.splitext( fname )[0]
	
	parse_name = base + '.parse'
	if os.path.exists( parse_name ):
		parsed = tree_parser.parse_file( fname )
		parse_dump = tree_parser.get_dump( parsed )
		with open( parse_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
		
		status( 'Parse', parse_dump == check_dump )
		
	yaml_name = base + '.yaml'
	if os.path.exists( yaml_name ):
		test = yaml.safe_load( open( yaml_name ).read() )
		if 'fail-parse' in test:
			try:
				_ = tree_parser.parse_file( fname )
				okay = False
			except Exception as e:
				okay = True
			status( 'Fail-Parse', okay )
			
			
	html_name = base + '.html'
	if os.path.exists( html_name ):
		doc = mdl.load_document( fname )
		writer = mdl.HtmlWriter()
		html = writer.write( doc )
		
		with open( html_name, 'r', encoding = 'utf-8' ) as check:
			check_html = check.read()
		
		status( 'HTML', html == check_html )
		
	print()
		
		
		
