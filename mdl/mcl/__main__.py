# -*- coding: utf-8 -*-
"""
	CLI for the MCL loader.
"""
from typing import *
import argparse, os, sys

from mdl import structure, ParseException


def main() -> None:
	cli_args = argparse.ArgumentParser( description = 'Process an MCL document' )

	cli_args.add_argument( 'mcl_file', metavar = 'input-file.mcl', nargs = '?', help='Input document' )
	cli_args.add_argument( '--write-json', nargs='?', metavar='filename',
		help='Write the structure to a JSON file' )
	cli_args.add_argument( '--dump', nargs='?', metavar='filename',
		help='Write debug structure to a file' )
		
	args = cli_args.parse_args()
	
	if args.mcl_file:
		print( f'Loading MCL {args.mcl_file}' )
		try:
			obj = structure.structure_load( args.mcl_file )
		except ParseException as e:
			print(e.format_line())
			print(e.get_context())
			sys.exit(1)
			
		
		if args.write_json:
			print( f'Writing JSON {args.write_json}' )
			json = structure.structure_format_json( obj, pretty = True )
			with open( args.write_json, 'w', encoding='utf-8' ) as out_file:
				out_file.write( json )
				
		if args.dump:
			print( f'Writing Dump {args.dump}' )
			dump = structure.dump_structure( obj )
			with open( args.dump, 'w', encoding='utf-8' ) as out_file:
				out_file.write( dump )
	
main()
