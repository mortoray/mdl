from . import tree_parser, parse_to_doc, doc_process, doc_tree, doc_tree_dump, structure, parse_tree_dump
from typing import *

class Document:
	def __init__(self ):
		self.root : Optional[doc_tree.RootSection] = None
		self.meta : structure.ObjectType = {}
		self.sub : List[Document] = []
		
	def set_root( self, node : doc_tree.RootSection ) -> None:
		self.root = node
		
	def set_meta( self, meta : structure.ObjectType ) -> None:
		self.meta = meta
		
	def find_first_sub( self, match : Callable[['Document'],bool] ) -> Optional['Document']:
		for sub in self.sub:
			if match( sub ):
				return sub
		return None

def dump_document( doc : Document, *, _first = True ) -> str:
	text = ''
	if doc.meta:
		text += "+++\n"
		text += structure.dump_structure( doc.meta ) 
		text += "+++\n"
	elif not _first:
		text += "+++\n"
	if doc.root is not None:
		text += doc_tree_dump.get_node( doc.root )
	
	for sub in doc.sub:
		text += dump_document( sub, _first = False )
	return text
		
def load_document( path : str, *, 
	_dump_parse = False,
	_write_parse = None,
	_write_doc = None,
	_write_predoc = None,
	_dump_predoc = False,
	_dump_doc = False,
	_process = True
	) -> Document:
	
	tp = tree_parser.TreeParser()
	node = tp.parse_file( path )
	if _dump_parse:
		parse_tree_dump.dump( node )
	if _write_parse:
		with open( _write_parse, 'w', encoding = 'utf-8' ) as out:
			out.write( parse_tree_dump.get_dump( node ) )
	
	assert node.type == tree_parser.NodeType.container
	assert not node.sub_is_empty()
	
	doc = Document()
	
	matter = node.iter_sub()[0]
	if matter.type == tree_parser.NodeType.matter:
		meta = structure.structure_parse( matter.text, matter.location )
		doc.set_meta( meta )
		node.remove_sub_at( 0 )
		
	# Split into sub-documents
	cur_doc = doc
	scan_node = node
	while True:
		scan_iter = scan_node.iter_sub()
		new_doc = False
		for index in range(len(scan_iter)):
			matter = scan_iter[index]
			if matter.type == tree_parser.NodeType.matter:
				next_scan = scan_node.split_at( index )
				
				root = parse_to_doc.convert( scan_node )
				cur_doc.set_root( root )
				
				cur_doc = Document()
				doc.sub.append( cur_doc )
				new_doc = True
				
				meta = structure.structure_parse( matter.text, matter.location )
				cur_doc.set_meta( meta )
				next_scan.remove_sub_at( 0 )

				scan_node = next_scan
				break
		
		if not new_doc:
			break
	
	root = parse_to_doc.convert( scan_node )
	cur_doc.set_root( root )
	
	if _dump_predoc:
		print( dump_document( doc ) )
	if _write_predoc:
		with open( _write_predoc, 'w', encoding = 'utf-8' ) as out:
			out.write( dump_document( doc ) )
	
	if _process:
		doc_process.doc_process( root )
		if _dump_doc:
			print( dump_document( doc ) )

		if _write_doc:
			with open( _write_doc, 'w', encoding = 'utf-8' ) as out:
				out.write( dump_document( doc ) )
		
	return doc
	
__all__ = [ 'Document', 'load_document', 'dump_document' ]
