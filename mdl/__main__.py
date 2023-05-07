# -*- coding: utf-8 -*-
"""
	CLI for the MDL processor.
"""
from typing import *
import argparse, os, sys, codecs
from pkg_resources import resource_listdir, resource_string

from mdl import  format_html, format_markdown, render, structure
from .document import load_document

class Output(NamedTuple):
	filename: str
	format: Dict


writerMap = {
	'HtmlWriter': format_html.HtmlWriter,
	'MarkdownWriter': format_markdown.MarkdownWriter,
}

def load_format(ref: str) -> Dict:
	data = resource_string(__package__, f'formats/{ref}.mcl')
	text = codecs.decode(data, 'utf-8')
	return structure.structure_parse(text)
	
def list_formats() -> None:
	format_files = resource_listdir(__package__, 'formats')
	for format_file in format_files:
		ref = os.path.splitext(format_file)[0]
		format = load_format(ref)
		print(f'{ref}: {format["name"]}')
		
	
def main() -> None:
	cli_args = argparse.ArgumentParser( description = 'Process an MDL document' )

	cli_args.add_argument( 'mdl_file', metavar = 'input-file.mdl', nargs = '?', help='Input document' )
	cli_args.add_argument( '--write', nargs=2, action='append', 
		metavar=('format', 'filename'),
		help='Write using format to filename' )
	cli_args.add_argument( '--list-formats', action='store_true', help='List the available formats' )

	debug = cli_args.add_argument_group( title='Maintainer Debugging Tools' )
	debug.add_argument( '--dump-parse', action='store_true', help='Dump the parse tree' )
	debug.add_argument( '--dump-predoc', action='store_true', help='Dump the pre-processing document tree' )
	debug.add_argument( '--dump-doc', action='store_true', help='Dump the final document tree' )
	debug.add_argument( '--write-parse', nargs=1, 
		metavar='filename',
		help='Write the parse output to a file')
	debug.add_argument( '--write-doc', nargs=1, 
		metavar='filename',
		help='Write the processed document output to a file' )
	debug.add_argument( '--write-predoc', nargs=1, 
		metavar='filename',
		help='Write the pre-processing document output to a file' )

	args = cli_args.parse_args()

	if args.list_formats:
		list_formats()
		
	outputs : List[Output] = []
	for (ref, filename) in (args.write or []):
		format = load_format(ref)
		outputs.append( Output( filename, format ))

	if args.mdl_file:
		mdl_file = args.mdl_file
			
		print( 'Loading MDL {}'.format( mdl_file ) )
		doc = load_document( mdl_file, 
			_dump_parse = args.dump_parse,
			_write_parse = args.write_parse[0] if args.write_parse else None,
			_write_doc = args.write_doc[0] if args.write_doc else None,
			_dump_predoc = args.dump_predoc,
			_dump_doc = args.dump_doc,
			_write_predoc = args.write_predoc[0] if args.write_predoc else None )

		for output in outputs:
			print( f'Writing {output.format["name"]} to {output.filename}' )
			writer = writerMap[output.format['render']](**output.format.get('args',{}))
			text = writer.render( doc )
			with open( output.filename, 'w', encoding = 'utf-8' ) as out_file:
				out_file.write( text )

			
main()
