# A rough test of formatting as HTML
__all__ = ['HtmlWriter']

from typing import *
from enum import Enum, auto

import io, html
from . import doc_tree, doc_loader, document, doc_tree
import pygments # type: ignore
from pygments import lexers, formatters # type: ignore
from pygments.lexers import php # type: ignore

def escape( text : str ) -> str:
	return html.escape(text)

class TFType(Enum):
	section = auto()

TFPair = Tuple[TFType,Optional[str]]

class TreeFormatter:
	def __init__(self):
		self._text = io.StringIO()
		self._cur_context : List[TFPair] = []
		self._context : List[List[TFPair]] = [ self._cur_context ]
		
	def section(self, open : str, close : Optional[str] ):
		self._text.write( open )
		self._cur_context.append( (TFType.section, close) )
		
	def end_section(self):
		s = self._cur_context.pop()
		assert s[0] == TFType.section
		if s[1] is not None:
			self._text.write( s[1] )
			
	def write( self, text : str ):
		self._text.write( text )

	def open_context( self ):
		self._cur_context = []
		self._context.append( self._cur_context )
	
	def end_context( self ):
		ctx = self._context.pop()
		for item in ctx:
			if item[1] is not None:
				self._text.write(item[1])
		self._cur_context = self._context[-1]
		
		
	@property
	def value(self) -> str:
		return self._text.getvalue()

class XmlFormatter(TreeFormatter):
	def __init__(self):
		super().__init__()
		
	def block(self, tag : str, attrs : Dict[str,str] = {} ):
		lead = f'<{tag}'
		for name, value in attrs.items():
			lead += f' {name}="{escape(value)}"'
		lead += f'>'
		self.section( lead, f'</{tag}>' )
	
	def end_block(self):
		self.end_section()
		
	def text(self, text : str ):
		self.write( escape(text) )
		
		
class HtmlWriter:
	def __init__(self):
		self._reset()
		
	def _reset(self):
		self.output = XmlFormatter()
		self.notes = []
		self.stack : List[doc_tree.Node] = []
		
	def write( self, doc : document.Document ) -> str:
		self.output.block( "html" )
		self.output.block( "head" )
		if 'title' in doc.meta:
			self.output.block( "title" )
			self.output.text( doc.meta['title'] )
			self.output.end_block()
			
		self.output.end_block()

		self.output.block( "body" )
		if doc.root is not None:
			doc.root.visit( self )
		self.output.end_block()
		self.output.end_block()
		
		self._write_notes()
		
		return self.output.value
		
	def write_body( self, doc : document.Document ) -> str:
		self._reset()
		if doc.root is not None:
			doc.root.visit( self )
		self._write_notes()
		return self.output.value
		
	def enter( self, node : doc_tree.Node, segment : int ) -> bool:
		self.output.open_context()
		res = self._write_node( node, segment )
		self.stack.append( node )
		return res
	
	def exit( self, node : doc_tree.Node, segment : int ) -> None:
		back = self.stack.pop()
		assert back == node
		self.output.end_context()
		
		
	def _write_node( self, node : doc_tree.Node, segment : int ) -> bool:
		result = False
		def q( type, func ):
			nonlocal result
			if isinstance( node, type ):
				result = func( node, segment )
				return True
			return False

		def fail():
			raise Exception( "Unknown node type", node )
		
		_ = \
			q( doc_tree.Block, self._write_block ) or \
			q( doc_tree.Code, self._write_code ) or \
			q( doc_tree.Inline, self._write_inline ) or \
			q( doc_tree.Link, self._write_link ) or \
			q( doc_tree.List, self._write_list ) or \
			q( doc_tree.ListItem, self._write_list_item ) or \
			q( doc_tree.Note, self._write_note ) or \
			q( doc_tree.Section, self._write_section ) or \
			q( doc_tree.Text, self._write_text ) or \
			q( doc_tree.Paragraph, self._write_paragraph ) or \
			q( doc_tree.Embed, self._write_embed ) or \
			fail()
			
		return result

			
	def _write_sub( self, node ):
		self._write_node_list( node.iter_sub() )
			
	def _write_node_list( self, list_ ):
		for sub in list_:
			self._write_node( sub, 0 )

	"""
		HTML Flow can contain inline elements or Text. For rendering we'll use this to collapse a single paragraph into inline text, which is the most expected output.
	"""
	def _write_flow( self, node_list ):
		first = True
		for node in node_list:
			if first and isinstance( node, doc_tree.Paragraph ):
				self._write_node_list( node.iter_sub() )
			else:
				self._write_node( node )
			
			first = False
	
	# TODO: yucky string constants 
	inline_map = {
		'italic': ( '<i>', '</i>' ),
		'bold': ( '<b>', '</b>' ),
		'code': ( '<code>', '</code>' ),
		'header': ( '<strong>', ':</strong>' ),
	}

	def _write_inline( self, node : doc_tree.Inline, segment : int ) -> bool:
		if node.feature == doc_tree.feature_none:
			return True
			
		html_feature = type(self).inline_map[node.feature.name]
		self.output.section( html_feature[0], html_feature[1] )
		return True
		
	def _write_block( self, node, segment ):
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
		elif node.class_ == doc_tree.block_promote:
			tag = 'div'
			class_ = 'promote'
			
		self.output.block( tag, { 'class': class_ } )
		return True
	
	def _is_flow( self, node ) -> bool:
		return isinstance( node, doc_tree.ListItem )
		
	def _write_paragraph( self, node, segment ):
		parent = self.stack[-1]
		if parent.len_sub() != 1 or not self._is_flow( parent ):
			self.output.block( 'p' )
		#else we collapse the paragraph in a flow parent
		return True
		
	def _write_section( self, node, segment ):
		level_adjust = 2
		
		if segment == 0 and node.level > 0:
			self.output.block( "section" )
			
		# TODO: yucky magic number
		if segment == 1 and node.title != None:
			self.output.block( f'h{node.level + level_adjust}' )
		return True
		
		
	def _write_text( self, node, segment ):
		self.output.text( node.text )
		return True

	def _write_link( self, node, segment ):
		# TODO: more escaping
		attrs = { 'href': node.url }
		if node.title:
			attrs['title'] = node.title
		self.output.block( 'a', attrs )
		return True

	def _write_note( self, node, segment ):
		self.notes.append( node )
		number = len(self.notes)
		self.output.write( "<sup class='note'><a href='#note-{}'>{}</a></sup>".format( number, number ) )
		return False

	def _write_notes( self ):
		if len(self.notes) == 0:
			return
			
		self.output.block( 'footer', { 'class': "notes" } )
		self.output.block( 'ol' )
		for index, note in enumerate(self.notes):
			self.output.block( 'li', { 'id': f'note-{index+1}' } )
			self._write_sub( note )
			self.output.end_block( )
		self.output.end_block()
		self.output.end_block()
		
	def _write_code( self, node, segment ):
		if node.class_ == '':
			block = '<div class="codehilite"><pre>' + escape( node.text ) + '</pre></div>'
		else:
			if node.class_ == "php" and not "<?php" in node.text:
				lexer = pygments.lexers.php.PhpLexer( startinline = True )
			else:
				lexer = pygments.lexers.get_lexer_for_filename( 'file.' + node.class_ )
			formatter = pygments.formatters.HtmlFormatter( cssclass = 'codehilite' )
			block = pygments.highlight( node.text, lexer, formatter )
		
		self.output.write( "<div class='codehilitewrap'>" )
		self.output.write( block )
		self.output.write( "</div>" )
		return True
		

	def _write_list( self, node, segment ):
		self.output.block( 'ul' )
		return True
		
	def _write_list_item( self, node, segment ):
		self.output.block( 'li' )
		return True
		

	def _write_embed( self, node, segment ):
		if node.class_ == doc_tree.EmbedClass.image:
			self.output.write( '<p class="embed">' )
			self.output.write( '<img src="{}"/>'.format( node.url ) )
			self.output.write( '</p>' )
			
		elif node.class_ == doc_tree.EmbedClass.abstract:
			doc = doc_loader.get_document_info( node.url )
			self.output.write( '<div class="embed-doc">' )
			self.output.write( '<h1><a href="{}">{}</a></h1>'.format( escape( node.url), escape(doc['title'] ) ) )
			self.output.write( '<p class="author"><a href="{}"><img src="{}"/>{}</a></p>'.format( 
				escape( doc['author_url'] ), escape( doc['author_pic'] ), escape( doc['author'] ) ) )
				
			self.output.write( '</div>' )
		else:
			#TODO: emit error/warning?
			pass
		
		return True
