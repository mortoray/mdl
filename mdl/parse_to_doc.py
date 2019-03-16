# Convert the parse tree to a document tree
from . import doc_tree
from . import tree_parser

def convert( node ):
	assert node.type == tree_parser.NodeType.container
	
	root = doc_tree.Section(0)
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

def _convert_inlines( node ):
	para_subs = []
	next_node = 0
	subs = node.iter_sub()
	while next_node < len(subs):
		(next_node, para) = _convert_inline( next_node, subs )
		if para != None:
			para_subs.append( para )
			
	return para_subs

def _convert_para( node ):
	para_subs = _convert_inlines( node )
		
	if node.class_.startswith( '#' ):
		para = doc_tree.Section( len(node.class_), para_subs )
	elif node.class_.startswith( '>' ):
		para = doc_tree.Block( doc_tree.block_quote )
		para.sub = para_subs
	else:
		class_ = None
		
		# TODO: probably all classes should be handled with annotations
		anno = node.get_annotation( "Blurb" )
		if anno != None:
			class_ = doc_tree.block_blurb
		else:
			class_ = doc_tree.block_paragraph
			
		para = doc_tree.Block( class_ )
		para.sub = para_subs
		
	return para
	
def _convert_inline( node_offset, nodes ):
	node = nodes[node_offset]
	node_offset += 1
	
	if node.type == tree_parser.NodeType.text:
		return (node_offset, doc_tree.Text( node.text ))
		
	if node.type == tree_parser.NodeType.inline:
		if node.class_ == '[':
			return (node_offset, _convert_link( node ))

		if node.class_ == '*':
			feature = doc_tree.feature_bold
		elif node.class_ == '_':
			feature = doc_tree.feature_italic
		else:
			raise Exception("Unknown feature", node.class_)
			
		block = doc_tree.Inline(feature)
		block.sub = _convert_inlines(node)
		
		return (node_offset, block)
		
	raise Exception("Unexpected node type" )

def _collapse_text( node ):
	#TODO: this is really rough for now
	text = ''
	for sub in node.iter_sub():
		text += sub.text
	return text


def _convert_link( node ):
	attrs = node.get_attrs()
	url = _collapse_text( attrs[0] ) #TODO: proper iter

	block = doc_tree.Link(url)
	block.sub = _convert_inlines(node)
		
	return block
	
