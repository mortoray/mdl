from . import tree_parser, parse_to_doc, doc_process, doc_tree

class Document:
	def __init__(self, root : doc_tree.Section ):
		self.root = root
		
		
def load_document( path : str ) -> Document:
	node = tree_parser.parse_file( path )
	doc = parse_to_doc.convert( node )
	doc_process.doc_process( doc )
	return Document( doc )
	
