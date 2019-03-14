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
		q( doc_tree.Quote, _write_quote ) or \
		q( doc_tree.Text, _write_text ) or \
		q( doc_tree.Link, _write_link ) or \
		q( doc_tree.Blurb, _write_blurb ) or \
		fail()

		
def _write_block( output, node ):
	_write_sub( output, node )
	
def _write_sub( output, node ):
	_write_list( output, node.sub )
		
def _write_list( output, list_ ):
	for sub in list_:
		_write_node( output, sub )

# TODO: yucky string constants 
inline_map = {
	'italic': 'i',
	'bold': 'b',
}

def _write_inline( output, node ):
	html_feature = inline_map[node.feature.name]
	output.write( "<{}>".format( html_feature ) )
	_write_sub( output, node )
	output.write( "</{}>".format( html_feature ) )
	
def _write_paragraph( output, node ):
	output.write( "<p>" )
	_write_sub( output, node )
	output.write( "</p>" )
	
def _write_section( output, node ):
	output.write( "<section>" )
	output.write( "<h{}>".format( node.level ) )
	_write_list( output, node.title )
	output.write( "</h{}>".format( node.level ) )
	
	_write_sub( output, node )
	output.write( "</section>" )

def _write_quote( output, node ):
	output.write( "<blockquote>" )
	_write_sub( output, node )
	output.write( "</blockquote>" )

def _write_blurb( output, node ):
	output.write( "<footer>" )
	_write_sub( output, node )
	output.write( "</footer>" )
	
def _write_text( output, node ):
	#TODO: Escaping of course
	output.write( node.text )

def _write_link( output, node ):
	# TODO: more escaping
	output.write( "<a href='{}'>".format( node.url ) )
	_write_sub(output, node)
	output.write( "</a>" )
