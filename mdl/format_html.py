# A rough test of formatting as HTML

import io
from . import doc_tree

def format_html( root ):
	return _HtmlWriter().write( root )

class _HtmlWriter(object):
	def __init__(self):
		self.output = io.StringIO()
		self.notes = []
		
	def write( self, root ):
		self.output.write( "<html>" )
		self._write_node( root )
		self.output.write( "</html>" )
		
		self._write_notes()
		
		return self.output.getvalue()
		
	# TODO: Does Python have a visitor pattern?
	# TODO: I sure miss C++ macro's here, how can I Reduce the duplication in PYthon?
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
			q( doc_tree.List, self._write_list ) or \
			fail()

			
	def _write_sub( self, node ):
		self._write_node_list( node.sub )
			
	def _write_node_list( self, list_ ):
		for sub in list_:
			self._write_node( sub )

	# TODO: yucky string constants 
	inline_map = {
		'italic': 'i',
		'bold': 'b',
		'code': 'code',
	}

	def _write_inline( self, node ):
		html_feature = type(self).inline_map[node.feature.name]
		self.output.write( "<{}>".format( html_feature ) )
		self._write_sub( node )
		self.output.write( "</{}>".format( html_feature ) )
		
	def _write_block( self, node ):
		tag = 'p'
		class_ = ''
		if node.class_ == doc_tree.block_quote:
			tag = 'blockquote'
		elif node.class_ == doc_tree.block_aside:
			tag = 'blockquote'
			class_ = 'aside'
		elif node.class_ == doc_tree.block_blurb:
			tag = 'footer'
			class_ = 'blurb'
			
		self.output.write( "<{} class='{}'>".format(tag, class_) )
		self._write_sub( node )
		self.output.write( "</{}>".format(tag) )
		
	def _write_section( self, node ):
		self.output.write( "<section>" )
		if node.title != None:
			self.output.write( "<h{}>".format( node.level ) )
			self._write_node_list( node.title )
			self.output.write( "</h{}>".format( node.level ) )
		
		self._write_sub(  node )
		self.output.write( "</section>" )
		
	def _write_text( self, node ):
		#TODO: Escaping of course
		self.output.write( node.text )

	def _write_link( self, node ):
		# TODO: more escaping
		self.output.write( "<a href='{}'>".format( node.url ) )
		self._write_sub( node)
		self.output.write( "</a>" )

	def _write_note( self, node ):
		self.notes.append( node )
		number = len(self.notes)
		self.output.write( "<sup class='note'><a href='#note-{}'>{}</a></sup>".format( number, number ) )

	def _write_notes( self ):
		if len(self.notes) == 0:
			return
			
		self.output.write( '<footer class="notes">' )
		self.output.write( '<ol>' )
		for index, note in enumerate(self.notes):
			self.output.write( '<li id="note-{}">'.format(index+1) )
			self._write_node( note.node )
			self.output.write( '</li>' )
		self.output.write( '</ol>' )
		self.output.write( '</footer>' )
		
	def _write_code( self, node ):
		self.output.write( '<pre>{}</pre>'.format( node.text ) )
		

	def _write_list( self, node ):
		self.output.write( '<ul>' )
		for sub in node.sub:
			assert isinstance( sub, doc_tree.Block ) # The only supported type
			assert sub.class_ == doc_tree.block_paragraph
			
			self.output.write( '<li>' )
			self._write_sub( sub )
			self.output.write( '</li>' )
		self.output.write( '</ul>' )
