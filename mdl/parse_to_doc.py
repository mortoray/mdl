# Convert the parse tree to a document tree
from . import doc_tree
from . import tree_parser

class _ConvertContext(object):
	def __init__(self):
		self.open_notes = {}

"""
An iterator for the nodes that allows for nested iteration and peeking.
"""
class _NodeIterator(object):
	def __init__(self, nodes):
		self._nodes = list( nodes )
		self._at = 0
		
	def if_next(self):
		if self._at < len(self._nodes):
			res = self._nodes[self._at]
			self._at += 1
			return res
		return None
		
	def peek_next(self):
		assert self._at < len(self._nodes)
		return self._nodes[self._at]
		
	def if_peek_next(self):
		if self._at >= len(self._nodes):
			return None
		return self._nodes[self._at]
		
	def next(self):
		assert self._at < len(self._nodes)
		res = self._nodes[self._at]
		self._at += 1
		return res
		
	def has_next(self):
		return self._at < len(self._nodes)
		
	
def convert( node ):
	assert node.type == tree_parser.NodeType.container
	
	ctx = _ConvertContext()
	root = doc_tree.Section(0)
	subs = _convert_blocks( ctx, _NodeIterator(node.iter_sub()) )
	root.add_subs( subs )
	
	return root
	
	
def _convert_blocks( ctx, nodes_iter ):
	out = []
	
	section_stack = []
	cur_out = out
	prev_in_section = None
	
	def append_block( para ):
		nonlocal cur_out, prev_in_section
		if isinstance(para, doc_tree.Section):
			while para.level <= len(section_stack):
				_ = section_stack.pop()
			
			if len(section_stack) > 0:
				cur_out = section_stack[-1]._sub #TODO: fix!
			else:
				cur_out = out
			
			cur_out.append( para )
			section_stack.append( para )
			cur_out = para._sub #TODO: Fix!
			prev_in_section = None if len(cur_out) == 0 else cur_out[-1]
		elif para != None:
			cur_out.append( para )
			prev_in_section = para

	
	while nodes_iter.has_next():
		node = nodes_iter.peek_next()

		if node.type == tree_parser.NodeType.raw:
			node = nodes_iter.next()
			code = doc_tree.Code(node.text, node.class_)
			append_block( code )
			
		elif node.type == tree_parser.NodeType.block:
			para = _convert_block( ctx, nodes_iter, prev_in_section )
			append_block( para )
				
		elif node.type == tree_parser.NodeType.container:
			para = _convert_block( ctx, nodes_iter, prev_in_section )
			append_block( para )
			
		else:
			raise Exception("Unexpected block type", node)
			
	return out

def _convert_inlines( ctx, node ):
	para_subs = []
	nodes_iter = _NodeIterator( node.iter_sub() )
	while nodes_iter.has_next():
		para = _convert_inline( ctx, nodes_iter )
		if para != None:
			para_subs.append( para )
			
	return para_subs

def _convert_block( ctx, nodes_iter, prev_in_section ):
	para = None
	
	while True:
		node = nodes_iter.next()
		if node.class_.startswith( '^' ):
			assert node.text in ctx.open_notes
			if len(para_subs) == 1:
				ctx.open_notes[node.text].node = para_subs[0]
			else:
				para = doc_tree.Paragraph()
				para._sub = para_subs
				ctx.open_notes[node.text].node = para
			
			del ctx.open_notes[node.text]
			return None
			
		if node.type == tree_parser.NodeType.block:
			para_subs = [ doc_tree.Paragraph( _convert_inlines( ctx, node ) ) ]
		else:
			para_subs = _convert_blocks( ctx, _NodeIterator(node.iter_sub() ))
			
		if node.class_.startswith( '#' ):
			para = doc_tree.Section( len(node.class_), para_subs  )
		elif node.class_.startswith( '>' ):
			para = doc_tree.Block( doc_tree.block_quote )
			para.sub = para_subs
		elif node.class_.startswith( '-' ):
			if isinstance( prev_in_section, doc_tree.List ):
				para_list = prev_in_section
				para = None
			else:
				para_list = doc_tree.List()
				para = para_list
				
			list_item = doc_tree.ListItem( )
			list_item.add_subs( para_subs )
			para_list.add_sub( list_item )
			
		else:
			# TODO: probably all classes should be handled with annotations
			blurb = node.get_annotation( "Blurb" )
			aside = node.get_annotation( "Aside" )
			if blurb != None:
				para = doc_tree.Block( doc_tree.block_blurb, para )
			elif aside != None:
				para = doc_tree.Block( doc_tree.block_aside, para  )
			else:
				print(para_subs)
				assert len(para_subs) == 1
				para = para_subs[0]
			
		return para
	
def _convert_inline( ctx, nodes_iter ):
	node = nodes_iter.next()
	
	if node.type == tree_parser.NodeType.text:
		return doc_tree.Text( node.text )
		
	if node.type == tree_parser.NodeType.inline:
		if node.class_ == '[':
			return _convert_link( ctx, node, nodes_iter )

		if node.class_ == '^':
			return _convert_note( ctx, node, nodes_iter )
			
		if node.class_ == '*':
			feature = doc_tree.feature_bold
		elif node.class_ == '_':
			feature = doc_tree.feature_italic
		elif node.class_ == '`':
			feature = doc_tree.feature_code
		else:
			raise Exception("Unknown feature", node.class_)
			
		block = doc_tree.Inline(feature)
		block.add_subs( _convert_inlines(ctx, node) )
		
		if len(node.text) != 0:
			assert len(block._sub) == 0
			block.add_sub( doc_tree.Text( node.text ) )
		
		return block
		
	raise Exception("Unexpected node type" )

def _convert_note( ctx, node, nodes_iter ):
	if len(node.text) > 0:
		if node.text in ctx.open_notes:
			raise Exception( "There's already a footnote reference with name {}".format( node.text ) )
		
		empty_note = doc_tree.Note(None) #incomplete for now
		ctx.open_notes[node.text] = empty_note
		return empty_note
		
	else:
		next_node = nodes_iter.next()
		
		link = _convert_link( ctx, next_node )
		return doc_tree.Note(link)


def _collapse_text( ctx, node ):
	#TODO: this is really rough for now
	text = ''
	for sub in node.iter_sub():
		text += sub.text
	return text


def _convert_link( ctx, node, nodes_iter ):
	url_node = nodes_iter.next()
	if url_node.class_ != '(':
		raise Exception( "Unexpected node following anchor: " + str(url_node) )
	url = url_node.text

	block = doc_tree.Link(url)
	block.sub = _convert_inlines(ctx, node)
		
	return block
	

