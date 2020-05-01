# -*- coding: utf-8 -*-
"""
	CLI for the MDL processor.
"""
from typing import *
import argparse, os

from mdl import  format_html, format_markdown, render
from .document import load_document

class Output(NamedTuple):
	filename: str
	writer: render.Writer
	
def main() -> None:
	cli_args = argparse.ArgumentParser( description = 'Process and MDL document' )

	cli_args.add_argument( 'mdl_file', metavar = 'mdl-file', nargs = 1, help='Input document' )
	cli_args.add_argument( '--write-html', nargs=1, help='Write an HTML formatted file' )
	cli_args.add_argument( '--write-markdown', nargs=1, help='Write a Markdown formatted file' )

	debug = cli_args.add_argument_group( title='Maintainer Debugging Tools' )
	debug.add_argument( '--dump-parse', action='store_const', const=True, help='Dump the parse tree' )
	debug.add_argument( '--dump-predoc', action='store_const', const=True, help='Dump the pre-processing document tree' )
	debug.add_argument( '--dump-doc', action='store_const', const=True, help='Dump the final document tree' )
	debug.add_argument( '--write-parse', nargs=1, help='Write the parse output to a file' )
	debug.add_argument( '--write-doc', nargs=1, help='Write the processed document output to a file' )
	debug.add_argument( '--write-predoc', nargs=1, help='Write the pre-processing document output to a file' )

	args = cli_args.parse_args()
	mdl_file = args.mdl_file[0]

	outputs : List[Output] = []
	if args.write_html:
		outputs.append( Output( args.write_html[0], format_html.HtmlWriter() ) )
	if args.write_markdown:
		outputs.append( Output( args.write_markdown[0], format_markdown.MarkdownWriter() ) )

	print( 'Loading MDL {}'.format( mdl_file ) )
	doc = load_document( mdl_file, 
		_dump_parse = args.dump_parse,
		_write_parse = args.write_parse[0] if args.write_parse else None,
		_write_doc = args.write_doc[0] if args.write_doc else None,
		_dump_predoc = args.dump_predoc,
		_dump_doc = args.dump_doc,
		_write_predoc = args.write_predoc[0] if args.write_predoc else None )

	for output in outputs:
		print( 'Writing {}'.format( output.filename ) )
		text = output.writer.render( doc )
		with open( output.filename, 'w', encoding = 'utf-8' ) as out_file:
			out_file.write( text )

			
main()
