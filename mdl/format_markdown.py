# A rough test of formatting as Markdown

import io
from . import doc_tree
from . import render
from .format_html import HtmlWriter

from typing import *

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
		
	def _get_node( self, node : doc_tree.BlockNode ) -> str:
		text = ""
		def q( match_type, func : Callable[[Any], str]) -> bool:
			nonlocal text
			if isinstance( node, match_type ):
				text = func( node )
				return True
			return False

		def fail():
			raise Exception( "Unknown node type", node )
		
		_ = \
			q( doc_tree.Block, self._get_block ) or \
			q( doc_tree.Code, self._get_code ) or \
			q( doc_tree.List, self._get_list ) or \
			q( doc_tree.Note, self._get_note ) or \
			q( doc_tree.Section, self._get_section ) or \
			q( doc_tree.Paragraph, self._get_paragraph ) or \
			q( doc_tree.Embed, self._get_embed ) or \
			fail()
			
		return text

			
	def _get_sub( self, node : doc_tree.BlockContainer ) -> str:
		return self._get_node_list( node._sub )
			
	def _get_node_list( self, list_ : Sequence[doc_tree.BlockNode] ) -> str:
		return "".join( [ self._get_node( sub ) for sub in list_ ] )
		

	inline_map = {
		"italic": "_",
		"bold": "*",
		"code": "`",
	}
	def _get_inline( self, node : doc_tree.Inline ) -> str:
		if node.feature == doc_tree.feature_code:
			# This is GitHub's style of escaping ticks inside ticks
			text = self._get_paragraph_flow( node )
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
			return "{}{}{}".format( fmt, self._get_paragraph_flow( node ), fmt )
		
	def _get_paragraph( self, node : Union[doc_tree.Paragraph, doc_tree.ParagraphElement] ):
		return '\n' + self._get_paragraph_flow( node ) + '\n'
		
	def _get_paragraph_flow( self, node : doc_tree.ElementContainer ) -> str:
		text = ''
		for sub in node.iter_sub():
			text += self._get_element( sub )
		return text
		
	def _get_element( self, elm : doc_tree.Element ) -> str:
		text = ""
		def q( match_type, func : Callable[[Any], str]) -> bool:
			nonlocal text
			if isinstance( elm, match_type ):
				text = func( elm )
				return True
			return False

		def fail():
			raise Exception( "Unknown node type", node )
		
		_ = \
			q( doc_tree.Inline, self._get_inline ) or \
			q( doc_tree.Link, self._get_link ) or \
			q( doc_tree.Text, self._get_text ) or \
			fail()
			
		return text
		

	def _get_quote( self, node : doc_tree.Block ) -> str:
		return "\n>{}\n".format( self._get_sub( node ) )

	def _get_blurb( self, node : doc_tree.Block ) -> str:
		return "\n----\n\n_{}_\n".format( self._get_sub( node ) )

	def _get_block( self, node : doc_tree.Block ) -> str:
		if node.class_ == doc_tree.block_quote:
			return self._get_quote( node )
		elif node.class_ == doc_tree.block_blurb:
			return self._get_blurb( node )
		#else:
		#	return self._get_paragraph( node )
		raise Exception( "Unrecognized block type", node.class_ )
		
		
	def _get_flow( self, nodes : Sequence[ doc_tree.BlockNode ] ) -> str:
		if len(nodes) == 1 and isinstance( nodes[0], doc_tree.Paragraph ):
			return self._get_paragraph_flow( nodes[0] )
			
		text = ''
		for node in nodes:
			text += self._get_node( node )
		return text
		
	def _get_section( self, node : doc_tree.Section ) -> str:
		text = "\n"
		if not node.title is None:
			text += "#" * node.level
			text += self._get_flow( node.title )
			text += "\n"
		
		return text + self._get_sub( node )
		
	def _get_text( self, node : doc_tree.Text ) -> str:
		#TODO: Escaping of course
		return node.text

	def _get_link( self, node : doc_tree.Link ) -> str:
		# TODO: more escaping
		return "[{}]({})".format( self._get_paragraph_flow(node), node.url )

	def _get_note( self, node : doc_tree.Note ) -> str:
		self.notes.append( node )
		number = len(self.notes)
		return "<sup>[{}](#note-{})</sup>".format( number, number )

	def _write_notes( self ) -> None:
		if len(self.notes) == 0:
			return
			
		self.output.write( '\n----\n\n' )
		for index, note in enumerate(self.notes):
			self.output.write( '{}. <a id="note-{}"></a>'.format(index+1, index+1) )
			self.output.write( self._get_node( note.node ) )
			self.output.write("\n")
			

	def _get_code( self, node : doc_tree.Code ) -> str:
		# TODO: escape
		return "\n```{}\n{}\n```\n".format( node.class_, node.text )

	def _get_list( self, node : doc_tree.List ) -> str:
		if not _is_simple_list( node ):
			writer = HtmlWriter()
			writer._write_node( node ) #TODO: private access
			return "\n" + writer.output.getvalue() + "\n"
			
		text = ""
		for sub in node.iter_sub():
			assert isinstance( sub, doc_tree.ListItem ) # The only supported type
			
			text += "\n- " 
			text += self._get_flow( sub._sub )
		text += "\n"
		return text
		
	def _get_embed( self, node : doc_tree.Embed ) -> str:
		if node.class_ == doc_tree.EmbedClass.image:
			return "\n![]({})\n".format( node.url )
		elif node.class_ == doc_tree.EmbedClass.abstract:
			# Only for dev.to, this'll need a configuration
			return "\n{{% post {} %}}\n".format( node.url )
		else:
			raise f"Unsupported embed {node.class_.name}"
		
		
def _count_longest_backtick_chain( text : str ) -> int:
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
	

def _is_simple_list( node : doc_tree.List ) -> bool:
	for sub in node.iter_sub():
		if not (sub.len_sub() == 1 and isinstance(sub.first_sub(), doc_tree.Paragraph)):
			return False
	return True
	
