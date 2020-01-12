from typing import *
from . import doc_tree

def doc_process( root : doc_tree.Node ) -> None:
	root.visit( doc_tree.StackVisitor(_process) )
	
def _process( node : doc_tree.Node, stack : List[doc_tree.Node] ) -> bool:
	if isinstance( node, doc_tree.Text ):
		_process_text( node, stack )
	if isinstance( node, doc_tree.Inline ):
		_process_inline( node, stack )
	return True
	
def _process_text( node : doc_tree.Text, stack : List[doc_tree.Node] ):
	pass

	
def _process_inline( node : doc_tree.Inline, stack : List[doc_tree.Node] ):
	pass
		
		
