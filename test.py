"""
	Test driver for document tests.
"""
from typing import Callable, Any
import os, sys
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
	
def test_mdl( fname: str ) -> None:
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
		
	check_directions( fname, base, parse_file=tp.parse_file )
			
	html_name = base + '.html'
	if os.path.exists( html_name ):
		doc = mdl.load_document( fname )
		writer = mdl.HtmlWriter()
		html = writer.render( doc )
		
		with open( html_name, 'r', encoding = 'utf-8' ) as check:
			check_html = check.read()
		
		status( 'HTML', html == check_html )
		
	print()
		
		
def check_directions( 
	fname: str, 
	base : str,
	*,
	parse_file: Callable[[str],Any]
) -> None:
	# Yaml was the historical name of these, kept to distinguish from .mcl in structures test
	directions_name = base + '.yaml'
	if os.path.exists( directions_name ):
		test = structure.structure_load( directions_name )
		fail_parse = test.get('fail-parse')
		if fail_parse is not None:
			try:
				parse_file( fname )
				okay = False
			except mdl.ParseException as e:
				okay = e.code == fail_parse
				if not okay:
					print( e.code, '!=', fail_parse)
			status( 'Fail-Parse', okay )
			
def test_mcl( fname: str ) -> None:		
	print( fname, end=' ')
	base = os.path.splitext( fname )[0]
	
	check_directions(fname, base, parse_file=structure.structure_load)
				
	json_name = base + '.json'
	if os.path.exists( json_name ):
		obj = structure.structure_load( fname )
		json = structure.structure_format_json( obj, pretty = True )
		
		with open( json_name, 'r', encoding = 'utf-8' ) as check:
			check_json = check.read()
			
		status( 'JSON', json == check_json )
		
	dump_name = base + '.dump'
	if os.path.exists( dump_name ):
		obj = structure.structure_load( fname )
		dump = structure.dump_structure( obj )
		
		with open( dump_name, 'r', encoding = 'utf-8' ) as check:
			check_dump = check.read()
			
		status( 'Dump', dump == check_dump )
		
	print()

def main() -> None:
	for fname in fs.find( 'test/docs', name_regex = r".*\.mdl" ):
		test_mdl( fname )
	for fname in fs.find( 'test/structures', name_regex = r".*\.mcl" ):
		test_mcl( fname )
	
	if bad_count > 0:
		print(failed(f"{bad_count} errors"))
		sys.exit(1)
		
main()
	
