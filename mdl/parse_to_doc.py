# Convert the parse tree to a document tree
from . import doc_tree
from . import tree_parser

def convert( node ):
	assert node.type == tree_parser.NodeType.container
	
	root = doc_tree.Block()
	root.sub = _convert_blocks( node.iter_sub() )
	
	return root
	
	
def _convert_blocks( nodes_iter ):
	out = []
	
	cur_out = out
	
	for node in nodes_iter:
		
		if node.text == None or len(node.text) == 0:
			cur_out.append( _convert_para(node) )
		else:
			pass
			
	return out

def _convert_para( node ):
	if node.class_.startswith( '#' ):
		para = doc_tree.Header( len(node.class_) )
	else:
		para = doc_tree.Paragraph()
	for sub in node.iter_sub():
		para.sub.append( _convert_inline( sub ) )
		
	return para
	
def _convert_inline( node ):
	if node.type == tree_parser.NodeType.text:
		return doc_tree.Text( node.text )
		
	if node.type == tree_parse.NodeType.inline:
		pass
		
	raise Exception("Unexpected node type" )

	
