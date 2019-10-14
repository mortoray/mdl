from . import tree_parser, parse_to_doc, doc_process, doc_tree, doc_tree_dump, structure

class Document:
	def __init__(self ):
		self.root : Optional[doc_tree.Section] = None
		self.meta : structure.ObjectType = {}
		
	def set_root( self, node : doc_tree.Section ) -> None:
		self.root = node
		
	def set_meta( self, meta : structure.ObjectType ) -> None:
		self.meta = meta
		
		
def load_document( path : str, *, 
	_dump_parse = False,
	_write_parse = None,
	_dump_pre_doc = False,
	_dump_doc = False
	) -> Document:
	node = tree_parser.parse_file( path )
	if _dump_parse:
		tree_parser.dump( node )
	if _write_parse:
		with open( _write_parse, 'w', encoding = 'utf-8' ) as out:
			out.write( tree_parser.get_dump( node ) )
	
	doc = Document()
	
	# TODO: split on matter, each a separate doc
	assert node.type == tree_parser.NodeType.container
	assert not node.sub_is_empty()
	matter = node.iter_sub()[0]
	if matter.type == tree_parser.NodeType.matter:
		meta = structure.parse_structure( matter.text )
		doc.set_meta( meta )
	
	
	root = parse_to_doc.convert( node )
	if _dump_pre_doc:
		doc_tree_dump.dump( root )
		
	doc_process.doc_process( root )
	if _dump_doc:
		doc_tree_dump.dump( root )
	
	doc.set_root( root )
	return doc
	
