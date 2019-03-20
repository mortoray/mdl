# A rough test of formatting as Markdown

import io
from . import doc_tree
from . import render

def format_markdown( root ):
	return MarkdownWriter().render(root)

"""
This is focused on dev.to flavoured Markdown at the moment, which seems pretty much similar to GitHub styled markdown. We'll have to add custom emitters for different markdown eventually (sharing a base class)
"""
class MarkdownWriter(render.Writer):

	def __init__(self):
		super()
		self.output = io.StringIO()
		self.notes = []
		
	def render(self, node):
		self._write_node( node )
		self._write_notes()
		return self.output.getvalue()
		
	def _write_node( self, node ):
		def q( type, func ):
			if isinstance( node, type ):
				func( node )
				return True
			return False

		def fail():
			raise Exception( "Unknown node type", node )
		
		_ = q( doc_tree.Inline, self._write_inline ) or \
			q( doc_tree.Section, self._write_section ) or \
			q( doc_tree.Block, self._write_block ) or \
			q( doc_tree.Text, self._write_text ) or \
			q( doc_tree.Link, self._write_link ) or \
			q( doc_tree.Note, self._write_note ) or \
			q( doc_tree.Code, self._write_code ) or \
			fail()

			
	def _write_sub( self, node ):
		self._write_list( node.sub )
			
	def _write_list( self, list_ ):
		for sub in list_:
			self._write_node( sub )
		

	inline_map = {
		"italic": "_",
		"bold": "*",
	}
	def _write_inline( self, node ):
		fmt = type(self).inline_map[node.feature.name]
		self.output.write( fmt )
		self._write_sub( node )
		self.output.write( fmt )
		
	def _write_paragraph( self, node ):
		self.output.write( "\n" )
		self._write_sub( node )
		self.output.write( "\n" )

	def _write_quote( self, node ):
		self.output.write( "\n>" )
		self._write_sub( node )
		self.output.write( "\n" )

	def _write_blurb( self, node ):
		self.output.write( "\n----\n\n_" )
		self._write_sub( node )
		self.output.write( "_\n" )

	def _write_block( self, node ):
		if node.class_ == doc_tree.block_quote:
			self._write_quote( node )
		elif node.class_ == doc_tree.block_blurb:
			self._write_blurb( node )
		else:
			self._write_paragraph( node )
		
		
	def _write_section( self, node ):
		self.output.write( "\n" )
		if node.title != None:
			self.output.write( "#" * node.level )
			self._write_list( node.title )
			self.output.write( "\n" )
		
		self._write_sub(  node )
		
	def _write_text( self, node ):
		#TODO: Escaping of course
		self.output.write( node.text )

	def _write_link( self, node ):
		# TODO: more escaping
		self.output.write( "[" )
		self._write_sub(node)
		self.output.write( "]({})".format( node.url ) )

	def _write_note( self, node ):
		self.notes.append( node )
		number = len(self.notes)
		self.output.write( "<sup>[{}](#note-{})</sup>".format( number, number ) )

	def _write_notes( self ):
		if len(self.notes) == 0:
			return
			
		self.output.write( '\n----\n\n' )
		for index, note in enumerate(self.notes):
			self.output.write( '{}. <a id="note-{}"></a>'.format(index+1, index+1) )
			self._write_node( note.node )
			self.output.write("\n")
			

	def _write_code( self, node ):
		self.output.write( "\n```\n" )
		self.output.write( node.text ) # TODO: escape
		self.output.write( "\n```\n" )
