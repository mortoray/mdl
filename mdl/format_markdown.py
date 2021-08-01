# A rough test of formatting as Markdown
__all__ = ['MarkdownWriter']

from . import doc_tree, document, render, tree_formatter
from .format_html import HtmlWriter
import regex as re # type: ignore

from typing import *

class MarkdownFormatter(tree_formatter.TreeFormatter):
	def __init__(self):
		super().__init__()
		
	def text(self, text: str):
		#TODO: Escape
		self.write( text )
		

class StackItem:
	def __init__(self, node : doc_tree.Node ):
		self.node = node
		self.is_flow = False
		
"""
This is focused on dev.to flavoured Markdown at the moment, which seems pretty much similar to GitHub styled markdown. We'll have to add custom emitters for different markdown eventually (sharing a base class)
"""
class MarkdownWriter(render.Writer):

	def __init__(self):
		super()
		self.output = MarkdownFormatter()
		self.notes = []
		self.stack : List[StackItem] = []
		
	def render(self, doc : document.Document ) -> str:
		if doc.root is not None:
			doc.root.visit( self )
			
		self._write_notes()
		return self.output.value
		
	def render_node( self, node : doc_tree.Node ) -> str:
		node.visit( self )
		return self.output.value
		
	def _render_node_children( self, node : doc_tree.Node ) -> str:
		node.visit_children( self )
		return self.output.value
		
	def enter( self, node : doc_tree.Node ) -> bool:
		self.output.open_context()
		self.stack.append( StackItem(node) )
		return self._write_node( node )
		
	def exit( self, node : doc_tree.Node ) -> None:
		back = self.stack.pop()
		assert back.node == node
		self.output.end_context()
		
	
	def _write_node( self, node : doc_tree.Node ) -> bool:
		result = False
		def q( match_type, func : Callable[[Any], bool]) -> bool:
			nonlocal result
			if isinstance( node, match_type ):
				result = func( node )
				return True
			return False

		def fail():
			raise Exception( "unknown-node-type", node )
		
		_ = \
			q( doc_tree.Block, self._write_block ) or \
			q( doc_tree.Code, self._write_code ) or \
			q( doc_tree.Embed, self._write_embed ) or \
			q( doc_tree.Inline, self._write_inline ) or \
			q( doc_tree.Link, self._write_link ) or \
			q( doc_tree.ListItem, self._write_list_item ) or \
			q( doc_tree.List, self._write_list ) or \
			q( doc_tree.Note, self._write_note ) or \
			q( doc_tree.Paragraph, self._write_paragraph ) or \
			q( doc_tree.Section, self._write_section ) or \
			q( doc_tree.SectionTitle, self._write_section_title ) or \
			q( doc_tree.Text, self._write_text ) or \
			q( doc_tree.BlockMark, self._write_block_mark ) or \
			fail()
			
		return result

			
	inline_map = {
		"italic": ( "_", "_" ),
		"bold": ( "**", "**" ),
		"code": ( "`", "`" ),
		"none": ( "", "" ),
		"header": ( "**", ":**" ),
	}
	def _write_inline( self, node : doc_tree.Inline ) -> bool:
		if node.feature == doc_tree.feature_code:
			def format( text ) -> str:
				tick_len = 1 + _count_longest_backtick_chain( text )
				ticks = '`' * tick_len
				pre = ticks
				post = ticks
				if len(text) > 0 and text[0] == '`':
					pre += ' '
				if len(text) > 0 and text[-1] == '`':
					post = ' ' + post
				return f"{pre}{text}{post}"
				
			self.output.capture( format )
		else:
			fmt = type(self).inline_map.get(node.feature.name)
			if fmt is None:
				raise Exception( "unknown-inline-feature", node.feature.name )
			
			def format( text ) -> str:
				flow = _split_flow( text )
				#MYPY: failing to see the if statement from above
				assert fmt is not None
				return f"{flow[0]}{fmt[0]}{flow[1]}{fmt[1]}{flow[2]}"
			
			self.output.capture( format )
			
		return True
		
	def _write_paragraph( self, node : Union[doc_tree.Paragraph, doc_tree.ParagraphElement] ) -> bool:
		parent = self.stack[-2]
		if (isinstance(parent.node,doc_tree.NodeContainer) and parent.node.len_sub() != 1) or not parent.is_flow:
			self.output.section( '','\n\n' )
		# else we collapse the paragraph in a flow parent
		return True
		
	def _write_quote( self, node : doc_tree.Block ) -> bool:
		self.stack[-1].is_flow = True
		self.output.section( '>', '\n\n' )
		return True

	def _write_blurb( self, node : doc_tree.Block ) -> bool:
		self.output.write( '----\n\n' )
		self.stack[-1].is_flow = True
		self.output.section( '_', '_\n\n' )
		return True

	def _write_aside( self, node : doc_tree.Block ) -> bool:
		self.stack[-1].is_flow = True
		self.output.section( '>💭 ', '\n\n' )
		return True
		
	def _write_promote( self, node : doc_tree.Block ) -> bool:
		self.stack[-1].is_flow = True
		self.output.section( '>', '\n\n' )
		return True
		 
	def _write_block( self, node : doc_tree.Block ) -> bool:
		if node.class_ == doc_tree.block_quote:
			return self._write_quote( node )
		elif node.class_ == doc_tree.block_blurb:
			return self._write_blurb( node )
		elif node.class_ == doc_tree.block_aside:
			return self._write_aside( node )
		elif node.class_ == doc_tree.block_promote:
			return self._write_promote( node )

		raise Exception( "unknown-block-type", node.class_.name )
		
	def _write_section( self, node : doc_tree.Section ) -> bool:
		return True
		
	def _write_section_title( self, node : doc_tree.SectionTitle ) -> bool:
		parent = self.stack[-2].node
		assert isinstance( parent, doc_tree.Section )
		self.output.section( f'{"#" * parent.level} ', '\n\n' )
		return True
		
	def _write_text( self, node : doc_tree.Text ) -> bool:
		self.output.text( node.text )
		return True

	def _write_link( self, node : doc_tree.Link ) -> bool:
		# TODO: more escaping
		self.output.section( '[', f']({node.url})' )
		return True
		
	def _write_note( self, node : doc_tree.Note ) -> bool:
		self.notes.append( node )
		number = len(self.notes)
		self.output.section( f'<sup>[{number}](#note-{number})', '</sup>' )
		return False

	def _write_notes( self ) -> None:
		if len(self.notes) == 0:
			return
			
		self.output.write( '\n----\n\n' )
		for index, note in enumerate(self.notes):
			self.output.write( '{}. <a id="note-{}"></a>'.format(index+1, index+1) )
			# TODO: This approach could be replaced with a separate visitor for formatting notes
			writer = MarkdownWriter()
			self.output.write( writer._render_node_children( note ) )
			self.output.write("\n")
			

	def _write_code( self, node : doc_tree.Code ) -> bool:
		# TODO: escape
		self.output.write( f"```{node.class_}\n{node.text}\n```\n\n" )
		return True

	def _write_list( self, node : doc_tree.List ) -> bool:
		# TODO: Fix this
		if not _is_simple_list( node ):
			writer = HtmlWriter()
			writer._write_node( node ) #TODO: private access
			self.output.section('', "\n" + writer.output.value + "\n")
			return True
			
		self.output.section( '', '\n' )
		return True
		
	def _write_list_item( self, node : doc_tree.ListItem ) -> bool:
		self.stack[-1].is_flow = True
		self.output.section( '- ', '\n' )
		return True
		
	def _write_embed( self, node : doc_tree.Embed ) -> bool:
		if node.class_ == doc_tree.EmbedClass.image:
			self.output.write( f"![]({node.url})\n\n" )
		elif node.class_ == doc_tree.EmbedClass.abstract:
			# Only for dev.to, this'll need a configuration
			self.output.write( f"{{% link {node.url} %}}\n\n" )
		else:
			raise Exception(f"Unsupported embed {node.class_.name}")
			
		return True
		
	def _write_block_mark( self, node : doc_tree.BlockMark ) -> bool:
		if node.class_ == doc_tree.MarkClass.minor_separator:
			self.output.write( '----' )
		else:
			assert False
		return True
		
		
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
	

_split_flow_re = re.compile( r'(\s*)(.*)(\s*)' )
"""
	Splits text into (leading whitespace, stripped text, trailing whitespace)
	This is needed for Markdown features where spaces break feature parsing
"""
def _split_flow( text : str ) -> Tuple[str, str, str]:
	match = _split_flow_re.match( text )
	assert match != None
	return ( match.group(1), match.group(2), match.group(3) )
