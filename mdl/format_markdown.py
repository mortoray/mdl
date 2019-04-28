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
		self.output.write( self._get_node( node ) )
		self._write_notes()
		return self.output.getvalue()
		
	def _get_node( self, node ):
		text = ""
		def q( type, func ):
			nonlocal text
			if isinstance( node, type ):
				text = func( node )
				return True
			return False

		def fail():
			raise Exception( "Unknown node type", node )
		
		_ = \
			q( doc_tree.Block, self._get_block ) or \
			q( doc_tree.Code, self._get_code ) or \
			q( doc_tree.Inline, self._get_inline ) or \
			q( doc_tree.Link, self._get_link ) or \
			q( doc_tree.List, self._get_list ) or \
			q( doc_tree.Note, self._get_note ) or \
			q( doc_tree.Section, self._get_section ) or \
			q( doc_tree.Text, self._get_text ) or \
			fail()
			
		return text

			
	def _get_sub( self, node ):
		return self._get_node_list( node.sub )
			
	def _get_node_list( self, list_ ):
		return "".join( [ self._get_node( sub ) for sub in list_ ] )
		

	inline_map = {
		"italic": "_",
		"bold": "*",
		"code": "`",
	}
	def _get_inline( self, node ):
		if node.feature == doc_tree.feature_code:
			# This is GitHub's style of escaping ticks inside ticks
			text = self._get_sub( node )
			tick_len = 1 + _count_longest_backtick_chain( text )
			ticks = '`' * tick_len
			pre = ticks
			post = ticks
			if len(text) > 0 and text[0] == '`':
				pre += ' '
			if len(text) > 0 and text[-1] == '`':
				post = ' ' + post
			return "{}{}{}".format( pre, text, post )
		else:
			fmt = type(self).inline_map[node.feature.name]
			return "{}{}{}".format( fmt, self._get_sub( node ), fmt )
		
	def _get_paragraph( self, node ):
		return "\n{}\n".format( self._get_sub( node ) )

	def _get_quote( self, node ):
		return "\n>{}\n".format( self._get_sub( node ) )

	def _get_blurb( self, node ):
		return "\n----\n\n_{}_\n".format( self._get_sub( node ) )

	def _get_block( self, node ):
		if node.class_ == doc_tree.block_quote:
			return self._get_quote( node )
		elif node.class_ == doc_tree.block_blurb:
			return self._get_blurb( node )
		else:
			return self._get_paragraph( node )
		
		
	def _get_section( self, node ):
		text = "\n"
		if node.title != None:
			text += "#" * node.level
			text += self._get_node_list( node.title )
			text += "\n"
		
		return text + self._get_sub(  node )
		
	def _get_text( self, node ):
		#TODO: Escaping of course
		return node.text

	def _get_link( self, node ):
		# TODO: more escaping
		return "[{}]({})".format( self._get_sub(node), node.url )

	def _get_note( self, node ):
		self.notes.append( node )
		number = len(self.notes)
		return "<sup>[{}](#note-{})</sup>".format( number, number )

	def _write_notes( self ):
		if len(self.notes) == 0:
			return
			
		self.output.write( '\n----\n\n' )
		for index, note in enumerate(self.notes):
			self.output.write( '{}. <a id="note-{}"></a>'.format(index+1, index+1) )
			self.output.write( self._get_node( note.node ) )
			self.output.write("\n")
			

	def _get_code( self, node ):
		# TODO: escape
		self.output.write( "\n```{}\n{}\n```\n".format( node.class_, node.text ) )

	def _get_list( self, node ):
		text = ""
		for sub in node.sub:
			assert isinstance( sub, doc_tree.Block ) # The only supported type
			assert sub.class_ == doc_tree.block_paragraph
			
			text += "\n- " 
			text += self._get_sub( sub )
		text += "\n"
		return text
		
		
def _count_longest_backtick_chain( text ):
	count = 0
	max_count = 0
	def update_max():
		nonlocal count, max_count
		max_count = max( count, max_count )
		count = 0
		
	for c in text:
		if c == '`':
			count += 1
		else:
			update_max()
	update_max()
			
	return max_count
	
