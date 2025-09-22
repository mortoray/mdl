"""
	CLI for the proofreading tool.
"""
import argparse, os, sys, shutil

from mdl import ParseException, format_mdl, doc_tree, structure
from mdl.document import load_document, Document

def main() -> None:
	cli_args = argparse.ArgumentParser( description = 'Proofreading tools for an MDL document' )
	
	cli_args.add_argument( 'mode', choices=['prepare', 'restore'], help="Choose to prepare for proofreading, or restore from result")
	cli_args.add_argument( 'mdl_file', help='File to modify' )
	cli_args.add_argument( '--output', type=str, help='Write MDL to this file instead of in-place' )
	
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

	if args.mode == 'prepare':
		doc.root.transform( Preparer(doc) )
	else:
		doc.root.transform( Restorer(doc) )
	
	writer = format_mdl.MdlWriter()
	text = writer.render( doc )
	out_file_name = args.output or mdl_file
	if args.output is None:
		# Extra files while I'm ensuring the safety of this
		backup_file = f"{mdl_file}.{args.mode}.bak"
		shutil.copy2( mdl_file, backup_file )
		print( f'Writing backup to {backup_file}' )
		
	with open( out_file_name, 'w', encoding='utf-8') as out_file:
		out_file.write( text )
	print( f'Saved to {out_file_name}.')
		
		
PREPARE_EMBED_PREFIX = "prepare-replace-"

class Preparer(doc_tree.TransformCallback):
	def __init__(self, document: Document) -> None:
		self.code_count = 0
		self.document = document
		
	def enter(self, node : doc_tree.Node ) -> bool:
		return True
		
	def exit(self, node : doc_tree.Node ) -> None:
		return
		
	def transform(self, node: doc_tree.Node ) -> tuple[doc_tree.TransformType, doc_tree.Node]:
		if isinstance( node, doc_tree.Code ):
			name = f"{PREPARE_EMBED_PREFIX}{self.code_count}"
			replace = doc_tree.Embed( doc_tree.EmbedClass.document, name)
			
			sub = Document()
			sub.meta =  { 'name': name }
			sub.root = doc_tree.RootSection()
			sub.root.add_sub( node )
			self.document.sub.append( sub )
			
			self.code_count += 1
			return doc_tree.TransformType.replace, replace
			
		return doc_tree.TransformType.retain, node

		
class Restorer(doc_tree.TransformCallback):
	def __init__(self, document: Document) -> None:
		self.document = document
		
	def enter(self, node : doc_tree.Node ) -> bool:
		return True
		
	def exit(self, node : doc_tree.Node ) -> None:
		return
		
	def transform(self, node: doc_tree.Node ) -> tuple[doc_tree.TransformType, doc_tree.Node]:
		if isinstance( node, doc_tree.Embed ) and node.url.startswith( PREPARE_EMBED_PREFIX ):
			restore_index = self.document.find_first_sub_index( lambda s: s.meta["name"] == node.url )
			if restore_index is None:
				raise Exception(f"missing-sub:{node.url}")
			restore = self.document.sub.pop(restore_index)
			
			assert restore.root.len_sub() == 1
			return doc_tree.TransformType.replace, restore.root.first_sub()
			
		return doc_tree.TransformType.retain, node
		
	
main()
