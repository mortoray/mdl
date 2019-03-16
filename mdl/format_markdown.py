# A rough test of formatting as Markdown

import io
from . import doc_tree

def format_markdown( root ):
	output = io.StringIO()
	_write_node( output, root )
	
	return output.getvalue()

def _write_node( output, node ):
	def q( type, func ):
		if isinstance( node, type ):
			func( output, node )
			return True
		return False

	def fail():
		raise Exception( "Unknown node type", node )
	
	_ = q( doc_tree.Inline, _write_inline ) or \
		q( doc_tree.Section, _write_section ) or \
		q( doc_tree.Block, _write_block ) or \
		q( doc_tree.Text, _write_text ) or \
		q( doc_tree.Link, _write_link ) or \
		fail()

		
def _write_sub( output, node ):
	_write_list( output, node.sub )
		
def _write_list( output, list_ ):
	for sub in list_:
		_write_node( output, sub )
	

inline_map = {
	"italic": "_",
	"bold": "*",
}
def _write_inline( output, node ):
	#TODO: map features, this is just a test here

	fmt = inline_map[node.feature.name]
	output.write( fmt )
	_write_sub( output, node )
	output.write( fmt )
	
def _write_paragraph( output, node ):
	output.write( "\n" )
	_write_sub( output, node )
	output.write( "\n" )

def _write_quote( output, node ):
	output.write( "\n>" )
	_write_sub( output, node )
	output.write( "\n" )

def _write_blurb( output, node ):
	output.write( "\n----\n\n_" )
	_write_sub( output, node )
	output.write( "_\n" )

def _write_block( output, node ):
	if node.class_ == doc_tree.block_quote:
		_write_quote( output, node )
	elif node.class_ == doc_tree.block_blurb:
		_write_blurb( output, node )
	else:
		_write_paragraph( output, node )
	
	
def _write_section( output, node ):
	output.write( "\n" )
	if node.title != None:
		output.write( "#" * node.level )
		_write_list( output, node.title )
		output.write( "\n" )
	
	_write_sub( output, node )
	
def _write_text( output, node ):
	#TODO: Escaping of course
	output.write( node.text )

def _write_link( output, node ):
	# TODO: more escaping
	output.write( "[" )
	_write_sub(output, node)
	output.write( "]({})".format( node.url ) )
