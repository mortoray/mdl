# A rough test of formatting as HTML
__all__ = ['HtmlWriter']

from typing import *

import html
from . import doc_tree, doc_loader, document, doc_tree, render, tree_formatter
import pygments # type: ignore
from pygments import lexers, formatters # type: ignore
from pygments.lexers import php # type: ignore

def escape( text : str ) -> str:
	return html.escape(text)
		

class XmlFormatter(tree_formatter.TreeFormatter):
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
		
		
class HtmlWriter(render.Writer):
	def __init__(
		self, *, 
		body_only: bool = False, 
		wordpress: bool = False, 
		body_start: Optional[str] = None, 
		body_end: Optional[str] = None,
		no_section: bool = False,
	):
		self._reset()
		self._body_only = body_only
		self._wordpress = wordpress
		self._body_start = body_start or ''
		self._body_end = body_end or ''
		self._no_section = no_section
		
	def _reset(self):
		self.output = XmlFormatter()
		self.notes = []
		self.stack : List[doc_tree.Node] = []
		
	def render( self, doc : document.Document ) -> str:
		self._reset()
		
		if not self._body_only:
			self.output.block( "html" )
			self.output.block( "head" )
			if 'title' in doc.meta:
				self.output.block( "title" )
				title = doc.meta['title']
				assert isinstance(title,str)
				self.output.text( title )
				self.output.end_block()
				
			self.output.end_block()

			self.output.block( "body" )
			
		self.output.write(self._body_start)
		if doc.root is not None:
			doc.root.visit( self )
		self.output.write(self._body_end)
			
		if not self._body_only:
			self.output.end_block()
			self.output.end_block()
		
		self._write_notes()
		
		return self.output.value
		
	def enter( self, node : doc_tree.Node ) -> bool:
		self.output.open_context()
		res = self._write_node( node )
		self.stack.append( node )
		return res
	
	def exit( self, node : doc_tree.Node ) -> None:
		back = self.stack.pop()
		assert back == node
		self.output.end_context()
		
		
	def _write_node( self, node : doc_tree.Node ) -> bool:
		result = False
		def q( type, func ):
			nonlocal result
			if isinstance( node, type ):
				result = func( node )
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
			q( doc_tree.SectionTitle, self._write_section_title ) or \
			q( doc_tree.Text, self._write_text ) or \
			q( doc_tree.Paragraph, self._write_paragraph ) or \
			q( doc_tree.Embed, self._write_embed ) or \
			q( doc_tree.BlockMark, self._write_block_mark ) or \
			fail()
			
		return result

			
	def _write_sub( self, node ):
		for sub in node.iter_sub():
			sub.visit( self )

	
	# TODO: yucky string constants 
	inline_map = {
		'italic': ( '<i>', '</i>' ),
		'bold': ( '<b>', '</b>' ),
		'code': ( '<code>', '</code>' ),
		'header': ( '<strong>', ':</strong>' ),
	}

	def _write_inline( self, node : doc_tree.Inline ) -> bool:
		if node.feature == doc_tree.feature_none:
			return True
			
		if node.feature == doc_tree.feature_latex:
			if self._wordpress:
				self.output.write('[latex]')
				# no escaping expecting in this block
				assert node.len_sub() == 1
				sub_node = node.first_sub()
				assert isinstance(sub_node, doc_tree.Text)
				self.output.write(sub_node.text)
				self.output.write('[/latex]')
				return False
			else:
				self.output.section( '<pre>', '</pre>')
				return True
			
		html_feature = type(self).inline_map[node.feature.name]
		self.output.section( html_feature[0], html_feature[1] )
		return True
		
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
		elif node.class_ == doc_tree.block_promote:
			tag = 'div'
			class_ = 'promote'
			
		self.output.block( tag, { 'class': class_ } )
		return True
	
	def _is_flow( self, node ) -> bool:
		return isinstance( node, doc_tree.ListItem )
		
	def _write_paragraph( self, node ):
		parent = self.stack[-1]
		assert isinstance(parent, doc_tree.NodeContainer)
		if parent.len_sub() != 1 or not self._is_flow( parent ):
			self.output.block( 'p' )
		#else we collapse the paragraph in a flow parent
		return True
		
	def _write_section( self, node ):
		if node.level > 0 and not self._no_section:
			self.output.block( "section" )
		return True
			
	def _write_section_title( self, node ):
		level_adjust = 2
		parent = self.stack[-1]
		assert isinstance( parent, doc_tree.Section )
		self.output.block( f'h{parent.level + level_adjust}' )
		return True
		
		
	def _write_text( self, node ):
		self.output.text( node.text )
		return True

	def _write_link( self, node ):
		# TODO: more escaping
		attrs = { 'href': node.url }
		if node.title:
			attrs['title'] = node.title
		self.output.block( 'a', attrs )
		return True

	def _write_note( self, node ):
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
		
	def _write_code( self, node ):
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
		

	def _write_list( self, node ):
		self.output.block( 'ul' )
		return True
		
	def _write_list_item( self, node ):
		self.output.block( 'li' )
		return True
		

	def _write_embed( self, node ):
		if node.class_ == doc_tree.EmbedClass.image:
			self.output.write( '<p class="embed">' )
			alt = f" alt=\"{escape(node.alt)}\"" if len(node.alt) > 0 else ""
			self.output.write( f'<img src="{node.url}"{alt}/>' )
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

	def _write_block_mark( self, node : doc_tree.BlockMark ) -> bool:
		if node.class_ == doc_tree.MarkClass.minor_separator:
			self.output.write( '<hr class="minor">' )
		else:
			assert False
		return True
