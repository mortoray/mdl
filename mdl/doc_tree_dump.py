from . import doc_tree
from typing import *

class Formatter:
	def __init__(self):
		self._text = ""
		self._indent = []
		self._indent_str = ""
		self._pending_indent = False
		self._has_line_text = False
		
	def indent(self, text = "\t"):
		self._indent.append( text )
		self._update_indent_str()
		self._pending_ident = True
		
	def unindent(self):
		self._end_line()
		_ = self._indent.pop()
		self._update_indent_str()
		
	def _update_indent_str(self):
		self._indent_str = "".join(self._indent)

	def _start_indent(self):
		if self._pending_indent:
			self._text += self._indent_str
			self._pending_indent = False

	def _end_line(self):
		if self._has_line_text:
			self._has_line_text = False
			self._text += '\n'
			self._pending_indent = True
			
	def write_line(self, text):
		self._end_line()
		self._start_indent()
		self._text += text
		self._text += '\n'
		self._pending_indent = True
		
	def write( self, text ):
		self._start_indent()
		self._text += text
		self._has_line_text = True
		
	def end(self):
		self._end_line()
		
	@property 
	def text(self):
		return self._text
	
class DumpVisitor:
	def __init__(self):
		self.output = Formatter()
		
	def enter( self, node : doc_tree.Node, segment : int ) -> bool:
		if segment == 0:
			self._write(node)
		
		if isinstance( node, doc_tree.BlockNode ):
			if segment > 0:
				self.output.indent('|')
			else:
				self.output.indent()

		return True
		
	def exit( self, node : doc_tree.Node, segment : int ) -> None:
		if segment == 0:
			if isinstance( node, doc_tree.Inline ) or isinstance( node, doc_tree.Link ):
				self.output.write( "｣" )
			if isinstance( node, doc_tree.Note ):
				self.output.write( '}' )
			
		if isinstance( node, doc_tree.BlockNode ):
			self.output.unindent()
			
	def _write(self, node) -> None:
		def q( node_type, call ):
			if isinstance( node, node_type ):
				call( node )
				return True
			return False
			
		has = \
			q( doc_tree.Section, self.get_section ) or \
			q( doc_tree.Inline, self.get_inline ) or \
			q( doc_tree.Link, self.get_link ) or \
			q( doc_tree.Note, self.get_note ) or \
			q( doc_tree.List, self.get_list ) or \
			q( doc_tree.ListItem, self.get_list_item ) or \
			q( doc_tree.Block, self.get_block ) or \
			q( doc_tree.Text, self.get_text ) or \
			q( doc_tree.Paragraph, self.get_paragraph ) or \
			q( doc_tree.Embed, self.get_embed ) or \
			q( doc_tree.Code, self.get_code ) or \
			q( doc_tree.Token, self.get_token )
		
		if not has:
			raise Exception( "Unsupported type", node )
	
	def get_block(self, node) -> None:
		self.output.write_line( f"<Block:{node.class_.name}>" )
		
	def get_paragraph(self, node) -> None:
		self.output.write_line( "<Paragraph>" )
		
	def get_text(self, node):
		self.output.write( node. text )

	def get_code(self, node : doc_tree.Code):
		self.output.write_line( f"<Code:{node.class_}>" )
		self.output.indent()
		for line in node.text.split( "\n" ):
			self.output.write_line( line )
		self.output.unindent()
			
	def get_flow(self, nodes : Sequence[doc_tree.BlockNode]):
		pass
		#text = ''
		#for node in nodes:
		#	text += get( node, indent )
		#return text

	def get_section(self, node : doc_tree.Section):
		self.output.write_line( f'<Section:{node.level}>' )
		# TODO: visitor needs to allow overriding sub-flow
		#if node.title:
		#	text += '{}\n'.format( get_flow(node.title, indent + '\t|') )
		
	def get_inline(self, node):
		self.output.write( f'⁑{node.feature.name}｢' )

	def get_link(self, node):
		self.output.write( '⁑link｢' )
		self.output.write( f'url={node.url}' )
		if node.title:
			self.output.write( f';title={node.title}' )
		self.output.write( '｣｢' )

	def get_note(self, node):
		self.output.write( '^{' )
		
	def get_list(self, node):
		self.output.write_line( '<List>' )
		
	def get_list_item(self, node):
		self.output.write_line( '<ListItem>' )

	def get_embed(self, node):
		self.output.write_line( f'<Embed:{node.class_.name}> {node.url}' )

	def get_token(self, node):
		self.output.write( f'<Token {" ".join(node.args)}>' )
		
def get_node(node):
	dv = DumpVisitor()
	node.visit( dv )
	dv.output.end()
	return dv.output.text
	

