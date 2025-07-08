__all__ = ['MdlWriter']

import typing
from . import render, tree_formatter, document, doc_tree, structure

class MdlFormatter(tree_formatter.TreeFormatter):
	def __init__(self):
		super().__init__()
		
	def text( self, text: str) -> None:
		self.write(text )
		
	def args( self, texts: list[str]) -> None:
		self.write( " ".join( self.escape_arg(text) for text in texts ) )
	
	def escape_arg( self, text: str )-> str:
		# TODO: This escaping is not good enough
		if not " " in text:
			return text
		return '"' + text + '"'
		
	
def indent_lines(text: str) -> str:
	return "".join('\t' + line + '\n' for line in text.splitlines())
	
class StackItem:
	def __init__(self, node : doc_tree.Node ):
		self.node = node
		self.is_flow = False
		self.child_count = 0
	
class MdlWriter(render.Writer):
	def __init__(self):
		super()
		self.output = MdlFormatter()
		self.stack : typing.List[StackItem] = []
		self.unsupported = False
		self.has_line_end = False
		self.first_paragraph = True
		
	def render(self, doc: document.Document ) -> str:
		if len(doc.meta) > 0:
			self.output.write("+++\n")
			self.output.write(structure.dump_structure( doc.meta ))
			self.output.write("+++\n\n")
			
		doc.root.visit( self )
		return self.output.value

	def enter( self, node : doc_tree.Node ) -> bool:
		self.output.open_context()
		self.stack.append( StackItem(node) )
		if len(self.stack) > 1:
			parent_item = self.stack[-2]
			parent_item.child_count += 1
			
			# this is the only thing that supports indented flow
			if isinstance( parent_item.node, doc_tree.ListItem ):
				if parent_item.child_count > 2:
					self.output.write('\n')
				if parent_item.child_count > 1:
					self.output.capture( indent_lines )
			elif isinstance(parent_item.node, doc_tree.List ):
				# single line outputs are fine
				pass
			elif isinstance(parent_item.node, doc_tree.BlockContainer):
				if not self.first_paragraph:	
					self.output.write(f'\n')
				self.first_paragraph = False
			
		self.has_line_end = False
		return self._write_node( node )
		
	def exit( self, node : doc_tree.Node ) -> None:
		back = self.stack.pop()
		assert back.node == node
		if isinstance(node, doc_tree.BlockNode):
			if not self.has_line_end:
				self.output.write('\n')
			self.has_line_end = True
			
		self.output.end_context()

		
	def _write_node( self, node : doc_tree.Node ) -> bool:
		result = False
		def q( match_type, func : typing.Callable[[typing.Any], bool]) -> bool:
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
			q( doc_tree.NoteDefn, self._write_note_defn) or \
			q( doc_tree.Paragraph, self._write_paragraph ) or \
			q( doc_tree.RootSection, self._write_root_section ) or \
			q( doc_tree.Section, self._write_section ) or \
			q( doc_tree.SectionTitle, self._write_section_title ) or \
			q( doc_tree.Text, self._write_text ) or \
			q( doc_tree.BlockMark, self._write_block_mark ) or \
			fail()
			
		return result
		
	def _write_block_comment( self, node: doc_tree.Node ) -> None:
		if node.comment is not None:
			self.output.write( "/" )
			self.Unsupported = True
			#self._write_node( node.comment[0] )
	
	def _write_block( self, node : doc_tree.Block ) -> bool:
		self._write_block_comment( node )
		match node.class_:
			case doc_tree.block_quote:
				self.output.write('> ')
			case doc_tree.block_blurb:
				self.output.write('@Blurb\n')
			case doc_tree.block_aside:
				self.output.write('@Aside\n')
			case doc_tree.block_promote:
				self.output.write('@Promote\n')
			case doc_tree.block_custom:
				self.output.write('@Custom\n')
			case _:
				raise Exception( "unknown-block-type", node.class_.name )
			
		return True
		
	inline_map = {
		"italic": ("_", "_"),
		"bold": ("*", "*"),
		"code": ("`", "`" ),
		"none": ("", ""),
		"header": ("", "::"),
	}
	def _write_inline( self, node : doc_tree.Inline ) -> bool:
		# Code handling (escape)
		fmt = type(self).inline_map.get(node.feature.name)
		if fmt is None:
			raise Exception( "unknown-inline-feature", node.feature.name )

		self.output.section( fmt[0], fmt[1] )
		return True

	def _write_embed( self, node : doc_tree.Embed ) -> bool:
		return True

	def _write_paragraph( self, node : doc_tree.Paragraph ) -> bool:
		self._write_block_comment( node )
		return True
		
	def _write_root_section( self, node: doc_tree.RootSection ) -> bool:
		return True
		
	def _write_section( self, node : doc_tree.Section ) -> bool:
		return True
		
	def _write_section_title( self, node : doc_tree.SectionTitle ) -> bool:
		parent = self.stack[-2].node
		assert isinstance( parent, doc_tree.Section )
		self.output.write( f'{"#" * parent.level} ' )
		return True
		
	def _write_text( self, node : doc_tree.Text ) -> bool:
		out = node.text.replace( '—', '--' )
		self.output.text( out )
		return True

	def _write_link( self, node : doc_tree.Link ) -> bool:
		# TODO: more escaping
		self.output.section( '[', f']({node.url})' )
		return True
		
	def _write_note( self, node : doc_tree.Note ) -> bool:
		self.output.write( f"^{node.text} " )
		return False
		
	def _write_note_defn( self, node: doc_tree.NoteDefn ) -> bool:
		self.output.write( f'^{node.text} ')
		return True

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
		return True
		
	def _write_list_item( self, node : doc_tree.ListItem ) -> bool:
		self.stack[-1].is_flow = True
		self.output.write( '- ' )
		return True
		
	def _write_embed( self, node : doc_tree.Embed ) -> bool:
		name_map = {
			doc_tree.EmbedClass.image: "image",
			doc_tree.EmbedClass.abstract: "abgstract",
		}
		self.output.write( f"{{% {name_map[node.class_]} ")
		self.output.args( [node.url, node.alt] )
		self.output.write( "}\n\n" )
		
		return False
		
	def _write_block_mark( self, node : doc_tree.BlockMark ) -> bool:
		if node.class_ == doc_tree.MarkClass.minor_separator:
			self.output.write( '----\n\n' )
		else:
			assert False
		return True
