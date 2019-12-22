# -*- coding: utf-8 -*-
"""
	CLI for the MDL processor.
"""
import argparse, os

from mdl import  format_html, format_markdown
from .document import load_document

cli_args = argparse.ArgumentParser( description = 'Process and MDL document' )

cli_args.add_argument( 'mdl_file', metavar = 'mdl-file', nargs = 1, help='Input document' )
cli_args.add_argument( '--write-html', nargs=1, help='Write an HTML formatted file' )
cli_args.add_argument( '--write-markdown', nargs=1, help='Write a Markdown formatted file' )

debug = cli_args.add_argument_group( title='Maintainer Debugging Tools' )
debug.add_argument( '--dump-parse', action='store_const', const=True, help='Dump the parse tree' )
debug.add_argument( '--dump-pre-doc', action='store_const', const=True, help='Dump the pre-processing document tree' )
debug.add_argument( '--dump-doc', action='store_const', const=True, help='Dump the final document tree' )
debug.add_argument( '--write-parse', nargs=1, help='Write the parse output to a file' )
debug.add_argument( '--write-doc', nargs=1, help='Write the document output to a file' )


args = cli_args.parse_args()
mdl_file = args.mdl_file[0]

print( 'Loading MDL {}'.format( mdl_file ) )
doc = load_document( mdl_file, 
	_dump_parse = args.dump_parse,
	_write_parse = args.write_parse[0] if args.write_parse else None,
	_write_doc = args.write_doc[0] if args.write_doc else None,
	_dump_pre_doc = args.dump_pre_doc,
	_dump_doc = args.dump_doc )

if args.write_html:
	filename = args.write_html[0] 
	print( 'Writing HTML to {}'.format( filename ) )
	html = format_html.HtmlWriter().write( doc )
	with open( filename, 'w', encoding = 'utf-8' ) as out_file:
		out_file.write( html )

if args.write_markdown:
	filename = args.write_markdown[0] 
	print( 'Writing Markdown to {}'.format( filename ) )
	markdown = format_markdown.format_markdown( doc.root )
	with open( filename, 'w', encoding = 'utf-8' ) as out_file:
		out_file.write( markdown )
