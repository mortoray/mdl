from typing import *
from . import doc_tree

def doc_process( root : doc_tree.Node ) -> None:
	stack : List[doc_tree.Node] = []
	def enter( node : doc_tree.Node ) -> bool:
		stack.append( node )
		return _process( node, stack )
	
	def exit( node : doc_tree.Node ) -> None:
		stack.pop()
		
	root.visit( (enter,exit) )

	
def _process( node : doc_tree.Node, stack : List[doc_tree.Node] ) -> bool:
	if isinstance( node, doc_tree.Text ):
		_process_text( node, stack )
	if isinstance( node, doc_tree.Inline ):
		_process_inline( node, stack )
	return True
	
_text_replace_map = {
	'--': '—',
}

def _process_text( node : doc_tree.Text, stack : List[doc_tree.Node] ):
	for src, dst in _text_replace_map.items():
		node.text = node.text.replace( src, dst )

	
def _process_inline( node : doc_tree.Inline, stack : List[doc_tree.Node] ):
	if node.feature == doc_tree.feature_header:
		# keep only for listitem headers
		if len(stack) > 3 and (isinstance(stack[-2], doc_tree.Paragraph) and isinstance(stack[-3], doc_tree.ListItem)):
			return
			
		# otherwise revert to normal text
		# TODO: provide a proper way to manipulate the tree
		node.feature = doc_tree.feature_none
		
		text = doc_tree.Text( ':' )
		node.add_sub(text)
		
		
