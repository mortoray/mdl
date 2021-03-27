"""
	Test driver for document tests.
"""
import os, yaml, sys
from mdl import tree_parser, parse_to_doc, format_html, doc_process, document, parse_tree_dump, structure
import mdl
from shelljob import fs #type: ignore

bad_count = 0

def passed(text : str) -> str:
	return '\x1b[32m{} ✔ \x1b[m'.format(text)

def failed(text : str) -> str:
	return '\x1b[31m{} ✗\x1b[m'.format(text)

def status(text, okay):
	global bad_count
	if not okay:
		bad_count += 1
	print( passed(text) if okay else failed(text), end=' ' )
	
for fname in fs.find( 'test/docs', name_regex = r".*\.mdl" ):
	print( fname, end= ' ' )
	base = os.path.splitext( fname )[0]
	
	tp = tree_parser.TreeParser()
	
	parse_name = base + '.parse'
	if os.path.exists( parse_name ):
		parsed = tp.parse_file( fname )
		parse_dump = parse_tree_dump.get_dump( parsed )
		with open( parse_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
		
		status( 'Parse', parse_dump == check_dump )
		
	doc_name = base + '.doc'
	if os.path.exists( doc_name ):
		doc = mdl.load_document( fname )
		doc_dump = document.dump_document( doc )
		with open( doc_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
			
		status( 'Doc', doc_dump == check_dump )
		
	predoc_name = base + '.predoc'
	if os.path.exists( predoc_name ):
		doc = mdl.load_document( fname, _process = False )
		doc_dump = document.dump_document( doc )
		with open( predoc_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
			
		status( 'PreDoc', doc_dump == check_dump )
		
	yaml_name = base + '.yaml'
	if os.path.exists( yaml_name ):
		test = yaml.safe_load( open( yaml_name ).read() )
		if 'fail-parse' in test:
			try:
				_ = tp.parse_file( fname )
				okay = False
			except Exception as e:
				okay = True
			status( 'Fail-Parse', okay )
			
			
	html_name = base + '.html'
	if os.path.exists( html_name ):
		doc = mdl.load_document( fname )
		writer = mdl.HtmlWriter()
		html = writer.render( doc )
		
		with open( html_name, 'r', encoding = 'utf-8' ) as check:
			check_html = check.read()
		
		status( 'HTML', html == check_html )
		
	print()
		
		
		
for fname in fs.find( 'test/structures', name_regex = r".*\.mcl" ):
	print( fname, end=' ')
	base = os.path.splitext( fname )[0]
	obj = structure.structure_load( fname )
	
	json_name = base + '.json'
	if os.path.exists( json_name ):
		json = structure.structure_format_json( obj, pretty = True )
		
		with open( json_name, 'r', encoding = 'utf-8' ) as check:
			check_json = check.read()
			
		status( 'JSON', json == check_json )
		
	dump_name = base + '.dump'
	if os.path.exists( dump_name ):
		dump = structure.dump_structure( obj )
		
		with open( dump_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
			
		status( 'Dump', dump == check_dump )
		
	print()
	
if bad_count > 0:
	print(failed(f"{bad_count} errors"))
	sys.exit(1)
	
