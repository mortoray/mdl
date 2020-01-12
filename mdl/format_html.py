# A rough test of formatting as HTML
__all__ = ['HtmlWriter']

from typing import *

import io, html
from . import doc_tree, doc_loader, document, doc_tree
import pygments # type: ignore
from pygments import lexers, formatters # type: ignore
from pygments.lexers import php # type: ignore

def escape( text : str ) -> str:
	return html.escape(text)

class TreeFormatter:
	def __init__(self):
		self._text = io.StringIO()
		self._context = []
		
	def section(self, open : str, close : Optional[str] ):
		self._text.write( open )
		self._context.append( close )
		
	def end_section(self):
		ctx = self._context.pop()
		if ctx is not None:
			self._text.write( ctx )
			
	def write( self, text : str ):
		self._text.write( text )
		
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
		
	def write( self, doc : document.Document ) -> str:
		self.output.block( "html" )
		self.output.block( "head" )
		if 'title' in doc.meta:
			self.output.block( "title" )
			self.output.text( doc.meta['title'] )
			self.output.end_block()
			
		self.output.end_block()

		self.output.block( "body" )
		self._write_node( doc.root )
		self.output.end_block()
		self.output.end_block()
		
		self._write_notes()
		
		return self.output.value
		
	def write_body( self, doc : document.Document ) -> str:
		self._reset()
		self._write_node( doc.root )
		self._write_notes()
		return self.output.value
		
		
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
		
		_ = \
			q( doc_tree.Block, self._write_block ) or \
			q( doc_tree.Code, self._write_code ) or \
			q( doc_tree.Inline, self._write_inline ) or \
			q( doc_tree.Link, self._write_link ) or \
			q( doc_tree.List, self._write_list ) or \
			q( doc_tree.Note, self._write_note ) or \
			q( doc_tree.Section, self._write_section ) or \
			q( doc_tree.Text, self._write_text ) or \
			q( doc_tree.Paragraph, self._write_paragraph ) or \
			q( doc_tree.Embed, self._write_embed ) or \
			fail()

			
	def _write_sub( self, node ):
		self._write_node_list( node.iter_sub() )
			
	def _write_node_list( self, list_ ):
		for sub in list_:
			self._write_node( sub )

	"""
		HTML Flow can contain inline elements or Text. For rendering we'll use this to collapse the first paragraph into inline text, which is the most expected output.
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

	def _write_inline( self, node : doc_tree.Inline ) -> None:
		if node.feature == doc_tree.feature_none:
			self._write_sub(node)
			return
			
		html_feature = type(self).inline_map[node.feature.name]
		self.output.section( html_feature[0], html_feature[1] )
		self._write_sub( node )
		self.output.end_section( )
		
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
		#TODO: self._write_flow( node.iter_sub() )  # Which makes sense, this is compacter, but often less correct?
		self._write_sub( node )
		self.output.end_block()
	
	def _write_paragraph( self, node ):
		self.output.block( 'p' )
		self._write_sub( node )
		self.output.end_block( )
		
		
	def _write_section( self, node ):
		level_adjust = 2
		
		if node.level > 0:
			self.output.block( "section" )
			
		if node.title != None:
			self.output.block( f'h{node.level + level_adjust}' )
			self._write_flow( node.title )
			self.output.end_block()
		
		self._write_sub(  node )
		if node.level > 0:
			self.output.end_block()
		
	def _write_text( self, node ):
		self.output.text( node.text )

	def _write_link( self, node ):
		# TODO: more escaping
		attrs = { 'href': node.url }
		if node.title:
			attrs['title'] = node.title
		self.output.block( 'a', attrs )
		self._write_sub( node)
		self.output.end_block()

	def _write_note( self, node ):
		self.notes.append( node )
		number = len(self.notes)
		self.output.write( "<sup class='note'><a href='#note-{}'>{}</a></sup>".format( number, number ) )

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
		

	def _write_list( self, node ):
		self.output.block( 'ul' )
		for sub in node.iter_sub():
			assert isinstance( sub, doc_tree.ListItem )
			
			self.output.block( 'li' )
			self._write_flow( sub.iter_sub() )
			self.output.end_block()
		self.output.end_block()

	def _write_embed( self, node ):
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
		
