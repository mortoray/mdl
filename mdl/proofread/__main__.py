"""
	CLI for the proofreading tool.
"""
import argparse, os, sys

from mdl import ParseException, format_mdl
from mdl.document import load_document

def main() -> None:
	cli_args = argparse.ArgumentParser( description = 'Proofreading tools for an MDL document' )
	
	cli_args.add_argument( 'mode', choices=['prepare', 'restore'], help="Choose to prepare for proofreading, or restore from result")
	cli_args.add_argument( 'mdl_file', help='File to modify' )
	
	debug = cli_args.add_argument_group( title='Maintainer Debugging Tools' )
	debug.add_argument( '--dump-doc', action='store_true', help='Dump the final document tree' )
	debug.add_argument( '--dump-parse', action='store_true', help='Dump the parse tree' )
	
	args = cli_args.parse_args()
	
	mdl_file = args.mdl_file
	print( f'Loading MDL {mdl_file}' )
	try:
		doc = load_document( mdl_file, _dump_doc = args.dump_doc, _dump_parse = args.dump_parse)
	except ParseException as e:
		print(e.format_line())
		print(e.get_context())
		sys.exit(1)
		
	writer = format_mdl.MdlWriter()
	text = writer.render( doc )
	print( text )
		
main()
