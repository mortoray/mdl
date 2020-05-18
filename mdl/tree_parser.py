# Tree parsing
from __future__ import annotations # type: ignore
import regex as re # type: ignore
from typing import *
from abc import abstractmethod
from enum import Enum, auto

from .source import Source
from .parse_tree import *

_syntax_empty_line = re.compile( r'[\p{Space_Separator}\t]*$', re.MULTILINE )
_syntax_inline_header = re.compile( r'::' )
_syntax_inline_note = re.compile( r'\^([\p{L}\p{N}]*)' )


class BlockLevelBuilder:
	def __init__(self, source : Source, parser : TreeParser, indent : str):
		self._annotations : List[Annotation] = []
		self._blocks : List[Node] = []
		self.source = source
		self._parser = parser
		self._indent = indent
		
	def append_annotation( self, anno : Annotation ) -> None:
		self._annotations.append( anno )
		
	def append_block( self, block ) -> None:
		block.add_annotations( self._annotations )
		self._annotations = []
		self._blocks.append( block )
		
	def parse_line( self, terminal : Optional[str] = None) -> Sequence[Node]:
		return self._parser._parse_line( self.source, terminal )
		
	def parse_para( self ) -> Node:
		return self._parser._parse_para( self.source, self._indent )
		
	def parse_args( self, close_char : str ) -> List[str]:
		return self._parser._parse_args( self.source, close_char )
	
class BlockLevelMatcher(Protocol):
	@abstractmethod
	def get_match_regex( self ) -> re.Pattern:
		raise NotImplementedError()
		
	@abstractmethod
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		raise NotImplementedError()
	
# A feature may have any regex opening match, but requires a single character terminal
class FeatureParse():
	class ContentType(Enum):
		parsed = auto()
		raw = auto()
		token = auto()
		
	open_pattern : str
	close_char : str
	content : Type
	
	@classmethod
	def open_close(class_, open_pattern, close_char ):
		fp = FeatureParse()
		fp.open_pattern = open_pattern
		fp.close_char = close_char
		fp.content = class_.ContentType.parsed
		return fp
		
	@classmethod
	def raw(class_, open_pattern, close_char ):
		fp = FeatureParse()
		fp.open_pattern = open_pattern
		fp.close_char = close_char
		fp.content = class_.ContentType.raw
		return fp
		
	@classmethod
	def token(class_, open_pattern, close_char ):
		fp = FeatureParse()
		fp.open_pattern = open_pattern
		fp.close_char = close_char
		fp.content = class_.ContentType.token
		return fp
		
	@property
	def is_raw(self):
		return self.content == self.ContentType.raw
	
	@property
	def is_token(self):
		return self.content == self.ContentType.token
	

class BLMAnnotation(BlockLevelMatcher):
	pattern = re.compile( r'@(\p{L}+)' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		builder.append_annotation( Annotation( match.group(1) ) )
		

class BLMLine(BlockLevelMatcher):
	pattern = re.compile( r'(#+|-)\s*' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		class_ = match.group(1)
		line = Node(NodeType.block)
		line.class_ = class_
		line.add_subs( builder.parse_line() )
		builder.append_block( line )

		
class BLMComment(BlockLevelMatcher):
	# // must be first, as it appears to be doing non-greedy matching
	pattern = re.compile( r'(//|/)\s*' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		if match.group(1) == '//':
			para = builder.parse_para()
			builder.append_annotation( Annotation( 'comment', para ) )
		else:
			line = Node(NodeType.block)
			line.add_subs( builder.parse_line() )
			builder.append_annotation( Annotation( 'comment', line) )
			

class BLMSeparator(BlockLevelMatcher):
	pattern = re.compile( r'----[^$\s]*' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		sep = Node(NodeType.block)
		_ = builder.parse_line() # TODO: don't allow anything
		sep.class_ = '----'
		builder.append_block( sep )
		

class BLMTag(BlockLevelMatcher):
	pattern = re.compile( r'{%\s+(\p{L}+)\s' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		para = Node(NodeType.block)
		para.class_ = match.group(1)
		args = builder.parse_args( '}' )
		para.add_args( args )
			
		builder.append_block( para )

		
class BLMBlock(BlockLevelMatcher):
	pattern = re.compile( r'(>|>>)\s*' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		class_ = match.group(1)
		para = builder.parse_para()
		para.class_ = match.group(1)
		builder.append_block( para )
	

class BLMFootnote(BlockLevelMatcher):
	pattern = re.compile( r'\^([\p{L}\p{N}]*)\s+' )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		para = builder.parse_para()
		para.class_ = '^'
		para.text = match.group(1)
		builder.append_block( para )
		
		
class BLMRaw(BlockLevelMatcher):
	pattern_open = re.compile( r'(```)' )
	pattern_close = re.compile( r'(^```)', re.MULTILINE )
	pattern_rest_line = re.compile( r'(.*)$', re.MULTILINE )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern_open
		
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		raw = Node(NodeType.raw)
		line_match = builder.source.match(self.pattern_rest_line)
		assert line_match != None
		end_match, raw_text = builder.source.to_match(self.pattern_close)
		assert end_match != None
		# Strip first and last newlines as they're part of the syntax
		raw.text = raw_text[1:-1]
		raw.class_ = line_match.group(1)
		builder.append_block( raw )
		

class BLMMatter(BlockLevelMatcher):
	pattern_open = re.compile( r'(^\+\+\+)', re.MULTILINE ) 
	pattern_end = re.compile( r'(^\+\+\+$)', re.MULTILINE )
	def get_match_regex( self ) -> re.Pattern:
		return self.pattern_open
	
	def process( self, builder : BlockLevelBuilder, match : re.Match ):
		matter = Node(NodeType.matter)
		end_match, raw_text = builder.source.to_match(self.pattern_end)
		assert end_match != None
		matter.text = raw_text
		builder.append_block( matter )
	
	
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
		
		self._block_level_matchers = [
			BLMAnnotation(),
			BLMSeparator(),
			BLMLine(),
			BLMComment(),
			BLMTag(),
			BLMBlock(),
			BLMFootnote(),
			BLMRaw(),
			BLMMatter(),
		]
		
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
			'{': FeatureParse.token('{','}'),
		}
		
		s = "|".join([re.escape(tok) for tok in self._syntax_feature_map.keys()])
		self._syntax_feature = re.compile(s)
	
	"""
		Parses a file
		@param filename The name of the file to parse
		@return A node representing the document
	"""
	def parse_file( self, filename : str ) -> Node:
		in_source = Source.with_filename( filename )
	
		root = Node(NodeType.container)
		self._parse_container( root, in_source, '' )
		return root
	

	def _parse_container( self, root, src, indent ):
		builder = BlockLevelBuilder( src, self, indent )
			
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

			# Check all feature matches
			for blm in self._block_level_matchers:
				match = src.match( blm.get_match_regex() )
				if match != None:
					blm.process( builder, match )
					break
			
			#fallback to a normal paragraph
			else:
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
				elif feature_parse.is_token:
					feature_args = self._parse_args( src, feature_parse.close_char )
					feature.add_args( feature_args )
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
		
	def _parse_args( self, src : Source, close_char : str ) -> List[str]:
		result : List[str] = []
		
		#FEATURE: Add tuples, strings, matched blocks
		while True:
			src.skip_space()
			assert not src.is_at_end()
			
			c = src.peek_char()
			if c == '\"' or c == '\'':
				end = src.next_char()
				arg = src.parse_string( end )
				result.append(arg)
				
			elif c == close_char:
				_ = src.next_char()
				break
				
			else:
				arg = src.parse_token( [ close_char, '\"', '\'' ] )
				result.append(arg)
		
		return result
	
__all__ = [ 'TreeParser' ]
