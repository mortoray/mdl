# A rough test of formatting as HTML

import io
from . import doc_tree

def format_html( root ):
	output = io.StringIO()
	output.write( "<html>" )
	_write_node( output, root )
	output.write( "</html>" )
	
	return output.getvalue()

# TODO: Does Python have a visitor pattern?
# TODO: I sure miss C++ macro's here, how can I Reduce the duplication in PYthon?
def _write_node( output, node ):
	def q( type, func ):
		if isinstance( node, type ):
			func( output, node )
			return True
		return False

	def fail():
		raise Exception( "Unknown node type", node )
	
	_ = q( doc_tree.Inline, _write_inline ) or \
		q( doc_tree.Paragraph, _write_paragraph ) or \
		q( doc_tree.Section, _write_section ) or \
		q( doc_tree.Block, _write_block ) or \
		q( doc_tree.Text, _write_text ) or \
		fail()

		
def _write_block( output, node ):
	_write_sub( output, node )
	
def _write_sub( output, node ):
	_write_list( output, node.sub )
		
def _write_list( output, list_ ):
	for sub in list_:
		_write_node( output, sub )
	
def _write_inline( output, node ):
	pass
	
def _write_paragraph( output, node ):
	output.write( "<p>" )
	_write_sub( output, node )
	output.write( "</p>" )
	
	_write_sub( output, node )
	
def _write_section( output, node ):
	output.write( "<h{}>".format( node.level ) )
	_write_list( output, node.title )
	output.write( "</h{}>".format( node.level ) )
	
	_write_sub( output, node )
	
def _write_text( output, node ):
	#TODO: Escaping of course
	output.write( node.text )
