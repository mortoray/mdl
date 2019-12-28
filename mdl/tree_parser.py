# Tree parsing
from __future__ import annotations # type: ignore
import regex as re # type: ignore
from typing import *
from abc import abstractmethod

from .source import Source
from .parse_tree import *

_syntax_empty_line = re.compile( r'[\p{Space_Separator}\t]*$', re.MULTILINE )
_syntax_line = re.compile( r'(?!//)(#+|-|/)' )
_syntax_block = re.compile( r'(>|>>|//|\^([\p{L}\p{N}]*))\s*' )
_syntax_tag = re.compile( r'{%\s+(\p{L}+)\s' )
_syntax_raw = re.compile( r'(```)' )
_syntax_raw_end = re.compile( r'(^```)', re.MULTILINE )
_syntax_matter = re.compile( r'(^\+\+\+)', re.MULTILINE ) 
_syntax_matter_end = re.compile( r'(^\+\+\+$)', re.MULTILINE )
_syntax_annotation = re.compile( r'@(\p{L}+)' )
_syntax_rest_line = re.compile( r'(.*)$', re.MULTILINE )
_syntax_inline_header = re.compile( r'::' )
_syntax_inline_note = re.compile( r'\^([\p{L}\p{N}]*)' )

class BlockLevelBuilder:
	def __init__(self, source : Source, parser : TreeParser):
		self._annotations : List[Annotation] = []
		self._blocks : List[Node] = []
		self.source = source
		self._parser = parser
		
	def append_annotation( self, anno : Annotation ) -> None:
		self._annotations.append( anno )
		
	def append_block( self, block ) -> None:
		block.add_annotations( self._annotations )
		self._annotations = []
		self._blocks.append( block )
		
	def parse_line( self, terminal : Optional[str] = None) -> Sequence[Node]:
		return self._parser._parse_line( self.source, terminal )
	
class BlockLevelMatcher(Protocol):
	@abstractmethod
	def get_match_regex( self ) -> re.Pattern:
		raise NotImplementedError()
		
	@abstractmethod
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		raise NotImplementedError()
	
# A feature may have any regex opening match, but requires a single character terminal
class FeatureParse():
	is_raw : bool
	open_pattern : str
	close_char : str
	
	@classmethod
	def open_close(class_, open_pattern, close_char ):
		fp = FeatureParse()
		fp.open_pattern = open_pattern
		fp.close_char = close_char
		fp.is_raw = False
		return fp
		
	@classmethod
	def raw(class_, open_pattern, close_char ):
		fp = FeatureParse()
		fp.open_pattern = open_pattern
		fp.close_char = close_char
		fp.is_raw = True
		return fp
	

class BLMAnnotation(BlockLevelMatcher):
	def get_match_regex( self ) -> re.Pattern:
		return _syntax_annotation
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		builder.append_annotation( Annotation( match.group(1) ) )
		
_blm_annotation = BLMAnnotation()

class BLMLine(BlockLevelMatcher):
	def get_match_regex( self ) -> re.Pattern:
		return _syntax_line
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		class_ = match.group(1)
		line = Node(NodeType.block)
		line.class_ = class_
		line.add_subs( builder.parse_line() )
		
		if class_ == '/':
			line.class_ = ''
			builder.append_annotation( Annotation( 'comment', line) )
		else:
			builder.append_block( line )
			
_blm_line = BLMLine()
		

class TreeParser:
	def __init__(self):
		self._syntax_feature_map : Dict[str,FeatureParse] = {}
		self._syntax_feature : Optional[re.Pattern] = None

		self._text_replace_map : Dict[str,str] = {}
		self.add_text_replace( {
			'--': '—',
			'...': '…',
			# a test to ensure this plugin support would work
			':)': '☺',
		})
		
		self._init_features()

	def add_text_replace( self, reps : Dict[str,str] ) -> None:
		for src, dst in reps.items():
			assert src not in self._text_replace_map
			self._text_replace_map[src] = dst
			
		self._trp_regex = None
		
	def _get_trp_regex(self) -> re.Pattern:
		if self._trp_regex is None:
			res = "|".join([ re.escape(k) for k in self._text_replace_map.keys() ])
			self._trp_regex = re.compile( res )
		return self._trp_regex
		
	def _init_features(self) -> None:
		self._syntax_feature_map = {
			'*': FeatureParse.open_close('*','*'),
			'_': FeatureParse.open_close('_','_'),
			'`': FeatureParse.raw('`','`'),
			'[': FeatureParse.open_close('[',']'),
			'(': FeatureParse.raw('(',')'),
		}
		
		s = "|".join([re.escape(tok) for tok in self._syntax_feature_map.keys()])
		self._syntax_feature = re.compile(s)
	
	"""
		Parses a file
		@param filename The name of the file to parse
		@return A node representing the document
	"""
	def parse_file( self, filename : str ) -> Node:
		in_file = open( filename, 'r', encoding = 'utf-8' )
		in_text = in_file.read()
		in_source = Source(in_text)
	
		root = Node(NodeType.container)
		self._parse_container( root, in_source, '' )
		return root
	

	def _parse_container( self, root, src, indent ):
		builder = BlockLevelBuilder( src, self )
			
		while not src.is_at_end():
			if src.match( _syntax_empty_line ) != None:
				# TODO: It'd be preferable if the regex consumed the empty-line entirely
				src.next_char()
				continue
				
			(match_indent, lead_space) = src.match_indent( indent )
			if not match_indent:
				# TODO: add some strong rules about what's allowed here
				if len(lead_space) < len(indent):
					break
				if len(lead_space) > len(indent):
					assert len(builder._blocks) > 0
					child_container = builder._blocks[-1]
					child_container.promote_to_container()
					self._parse_container( child_container, src, lead_space )
					
				continue
			
			annotation_match = src.match( _blm_annotation.get_match_regex() )
			if annotation_match != None:
				_blm_annotation.process( builder, annotation_match )
				continue
				
			line_match = src.match( _blm_line.get_match_regex() )
			if line_match != None:
				_blm_line.process( builder, line_match )
				continue
				
			tag = src.match( _syntax_tag )
			if tag != None:
				para = Node(NodeType.block)
				para.class_ = tag.group(1)
				while True:
					arg, end = src.parse_string( '}' )
					if end: 
						break
					if arg is not None:
						para.add_arg( arg )
					
				builder.append_block( para )
				continue
				
				
			block = src.match( _syntax_block )
			if block != None:
				class_ = block.group(1)
				para = self._parse_para(src, indent)
				if class_ == '//':
					builder.append_annotation( Annotation( 'comment', para ) )
				else:
					para.class_ = block.group(1)
					
					# TODO: howto match two groups with a dpeendent group to avoid this?
					if class_[0:1] == '^':
						para.class_ = '^'
						para.text = block.group(2)
					builder.append_block( para )
				continue
				
			raw_match = src.match( _syntax_raw )
			if raw_match != None:
				raw = Node(NodeType.raw)
				line_match = src.match(_syntax_rest_line)
				assert line_match != None
				end_match, raw_text = src.to_match(_syntax_raw_end)
				assert end_match != None
				# Strip first and last newlines as they're part of the syntax
				raw.text = raw_text[1:-1]
				raw.class_ = line_match.group(1)
				builder.append_block( raw )
				continue
				
			matter_match = src.match( _syntax_matter )
			if matter_match != None:
				matter = Node(NodeType.matter)
				end_match, raw_text = src.to_match(_syntax_matter_end)
				assert end_match != None
				matter.text = raw_text
				builder.append_block( matter )
				continue
				
				
			para = self._parse_para(src, indent)
			# drop empty paragraphs
			if not para.sub_is_empty():
				builder.append_block( para )


		root.add_subs( builder._blocks )
		

	#TODO: unused?
	def _expand_false_node(self, node):
		assert len(node.text) == 0
		sub = []
		
		open_bit = Node( NodeType.text )
		open_bit.text = node.class_
		sub.append( open_bit )
				
		sub.extend( node.iter_sub() )
		
		close_bit = Node( NodeType.text )
		close_bit.text = self._syntax_feature_map[node.class_]
		sub.append( close_bit )
		return sub
		
		
	def _parse_line( self, src : Source, terminal : Optional[str] = None ) -> Sequence[Node]:
		bits : List[Node] = []
		text = ''
		end_char = terminal if terminal is not None else '\n'
		
		def end_text():
			nonlocal text
			if len(text) == 0:
				return
			
			n = Node(NodeType.text)
			n.text = text
			push_bit(n)
			text = ''
			
		def push_bits(bits):
			for bit in bits:
				push_bit(bit)
				
		def push_bit(bit):
			if bit.type == NodeType.text and len(bits) > 0 and bits[-1].type == NodeType.text:
				bits[-1].text += bit.text
			else:
				bits.append(bit)
				
		def mark_header():
			nonlocal bits
			at = 0
			while len(bits) > 0 and bits[at].class_ == '::':
				at += 1
				
			collect = bits[at:]
			bits = bits[:at]
			header = Node(NodeType.inline)
			header.class_ = '::'
			header.add_subs( collect )
			push_bit( header )
			
		def end_bits():
			pass
				
		has_end_char = False
		while not src.is_at_end():
			c = src.peek_char()
			if c == end_char:
				has_end_char = True
				_ = src.next_char()
				break
				
			if c == '\\':
				_ = src.next_char()
				text += src.next_char()
				continue
				
			note_match = src.match( _syntax_inline_note )
			if note_match is not None:
				note_name = note_match.group(1)
				end_text()
				note = Node( NodeType.inline )
				note.class_ = '^'
				note.text = note_name
				push_bit( note )
				continue
				
			header_match = src.match( _syntax_inline_header )
			if header_match is not None:
				end_text()
				mark_header()
				continue
				
			feature_match = src.match( self._syntax_feature )
			if feature_match is not None:
				feature_class = feature_match.group(0)
				end_text()
				
				feature_parse = self._syntax_feature_map[feature_class]
				
				feature = Node( NodeType.inline )
				feature.class_ = feature_class
				if feature_parse.is_raw:
					feature_text = self._parse_raw_escape_to( src, feature_parse.close_char )
					feature.text = feature_text
				else:
					feature_line = self._parse_line( src, feature_parse.close_char )
					feature.add_subs( feature_line )
				push_bit( feature )
				continue
				
				
			text += self._parse_char( src )
				
		if terminal is not None and not has_end_char:
			raise Exception( "unterminated-line-feature", end_char )
			
		end_text()
		end_bits()
		return bits

	def _parse_raw_escape_to( self, src, close_char ):
		start = src.position
		text = ''
		
		while not src.is_at_end():
			c = src.peek_char()
			if c == '\\':
				_ = src.next_char()
				c = src.next_char()
			elif c == close_char:
				_ = src.next_char()
				return text
			else:
				c = self._parse_char( src )
				
			text += c
			
		raise Exception( f"{src.map_position(start)} Unclosed raw text feature {close_char}" )


	"""	
		Parse the next textual character. This should be used in any place text is being constructed.
	"""
	def _parse_char( self, src : Source ) -> str:
		m = src.match( self._get_trp_regex() )
		if m is not None:
			return self._text_replace_map[m.group(0)]
		return src.next_char()
		
	def _parse_para( self, src : Source, indent : str ) -> Node:
		para = Node(NodeType.block)
		first = True
		while not src.is_at_end():
		
			# Parse Container preconsumes the leading space on the first entry to the paragraph, in order to do
			# other block matching. It's not sure how this can be avoided.
			if not first:
				if not src.match_indent( indent )[0]:
					break
			first = False
				
			line = self._parse_line(src)
			# Blank line ends the paragraph
			if len(line) == 0:
				break
			
			# Collapse consecutive text nodes
			if len(line) > 0 and line[0].type == NodeType.text:
				last = para.sub_last()
				if last != None and last.type == NodeType.text:
					last.text = last.text + ' ' + line[0].text
					line = line[1:]
			
			para.add_subs( line )
			
		return para
	
__all__ = [ 'TreeParser' ]
