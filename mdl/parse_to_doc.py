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
	
	section_stack = []
	cur_out = out
	
	for node in nodes_iter:

		para = _convert_para(node)
		if isinstance(para, doc_tree.Section):
			while para.level <= len(section_stack):
				_ = section_stack.pop()
			
			if len(section_stack) > 0:
				cur_out = section_stack[-1].sub
			else:
				cur_out = out
			
			cur_out.append( para )
			section_stack.append( para )
			cur_out = para.sub
		else:
			cur_out.append( para )
			
	return out

def _convert_para( node ):
	para_subs = []
	for sub in node.iter_sub():
		para_subs.append( _convert_inline( sub ) )
		
	if node.class_.startswith( '#' ):
		para = doc_tree.Section( len(node.class_), para_subs )
	else:
		para = doc_tree.Paragraph()
		para.sub = para_subs
		
	return para
	
def _convert_inline( node ):
	if node.type == tree_parser.NodeType.text:
		return doc_tree.Text( node.text )
		
	if node.type == tree_parser.NodeType.inline:
		block = doc_tree.Inline()
		for sub in node.iter_sub():
			block.sub.append( _convert_inline( sub ) )
		
		return block
		
	raise Exception("Unexpected node type" )

	
