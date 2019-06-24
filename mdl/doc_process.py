import typing
from . import doc_tree

def doc_process( root : doc_tree.Node ) -> None:
	root.visit( _process )

	
def _process( node : doc_tree.Node ) -> bool:
	if isinstance( node, doc_tree.Text ):
		_process_text( node )
	return True
	
_text_replace_map = {
	'--': '—',
}

def _process_text( node : doc_tree.Text ):
	for src, dst in _text_replace_map.items():
		node.text = node.text.replace( src, dst )

	
