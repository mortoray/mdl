# -*- coding: utf-8 -*-
"""
	CLI for the MCL loader.
"""
from typing import *
import argparse, os, sys

from mdl import structure


def main() -> None:
	cli_args = argparse.ArgumentParser( description = 'Process an MCL document' )

	cli_args.add_argument( 'mcl_file', metavar = 'input-file.mcl', nargs = '?', help='Input document' )
	cli_args.add_argument( '--write-json', nargs='?', metavar='filename',
		help='Write the structure to a JSON file' )
		
	args = cli_args.parse_args()
	
	if args.mcl_file:
		print( f'Loading MCL {args.mcl_file}' )
		obj = structure.structure_load( args.mcl_file )
		
		if args.write_json:
			print( f'Writing JSON {args.write_json}' )
			json = structure.structure_format_json( obj, pretty = True )
			with open( args.write_json, 'w', encoding='utf-8' ) as out_file:
				out_file.write( json )
	
main()
