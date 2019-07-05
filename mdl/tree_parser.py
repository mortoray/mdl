# Tree parsing
from __future__ import annotations # type: ignore
import regex as re # type: ignore
from typing import *

from enum import Enum

class NodeType(Enum):
	# may contain blocks and containers as children
	container = 1
	# may contain text and inline as children
	block = 2
	# text nodes may not have children
	text = 3
	# may contain text and inline as children
	inline = 4
	# may not contain children, text is the raw text
	raw = 5
	# may not contain children, data is the structured data
	matter = 6
	
class Annotation(object):
	def __init__(self, class_, node = None):
		self._class_ = class_
		self._node = node
		
	@property
	def class_( self ):
		return self._class_
		
	@property
	def node( self ):
		return self._node
		
class Node(object):
	def __init__(self, type):
		self._sub = []
		self._text = ''
		self._type = type
		self._class_ = ''
		self._attr = None
		self._annotations = None
		self._args = []
		self._data = None
		
	def __str__( self ):
		return "{}@{} \"{}\"".format( self._type, self._class_, self._text )
		
	def validate_sub( self, sub ):
		if self._type == NodeType.text:
			raise Exception( "The text type should not have children" )
		if self._type == NodeType.container and not sub._type in [NodeType.block, NodeType.raw, NodeType.container, NodeType.matter]:
			raise Exception( "containers can only contain blocks/raw" )
		if self._type in [NodeType.block, NodeType.inline] and not sub._type in [NodeType.inline, NodeType.text]:
			raise Exception( "blocks/inlines can only contain inline/text" )
			
		assert isinstance(sub, Node)
		
	def add_annotations( self, annotations ):
		if len(annotations) == 0:
			return
		if self._annotations == None:
			self._annotations = []
		self._annotations += annotations[:]
		
	def get_annotation( self, class_ ):
		if self._annotations == None:
			return None
		for anno in self._annotations:	
			if anno.class_ == class_:
				return anno
		return None
		
	def add_arg( self, arg : str):
		self._args.append( arg )
		
	def get_args( self ) -> List[str]:
		return self._args[:]
		
	def has_args( self ) -> bool:
		return len(self._args) > 0
		
	def promote_to_container( self ) -> None:
		first_child = Node( self._type )
		first_child._text = self._text
		self._text = ''

		first_child._sub = self._sub
		self._sub = [first_child]
		
		self._type = NodeType.container
		
	
	def add_subs( self, subs : Sequence[Node] ) -> None:
		for sub in subs:
			self.add_sub( sub )
			
	def add_sub( self, sub : Node ) -> None:
		self.validate_sub( sub )
		self._sub.append( sub )
			
	# As Python lacks a random access iterator, this returns a list view of the subs, it should not be modified
	def iter_sub( self ):
		return self._sub
		
	def sub_is_empty( self ):
		return len(self._sub) == 0
		
	def sub_last( self ):
		if len(self._sub) > 0:
			return self._sub[-1]
		return None
		
	@property
	def text(self):
		return self._text
		
	@text.setter
	def text( self, text ):
		assert isinstance(text, str)
		self._text = text
		
	@property
	def type( self ):
		return self._type

	@property
	def class_( self ):
		return self._class_
		
	@class_.setter
	def class_( self, value ):
		self._class_ = value
		
	def add_attr( self, node ):
		if self._attr == None:
			self._attr = []
		self._attr.append(node)
		
	def has_attr( self ):
		return self._attr != None and len(self._attr) > 0
		
	def iter_attr( self ):
		return iter(self._attr)
		
	def get_attrs(self):
		if self._attr == None:
			return []
		return self._attr
		
	def has_annotations( self ):
		return self._annotations != None and len(self._annotations) > 0
		
	def iter_annotations( self ):
		return iter( self._annotations )

_syntax_skip_space = re.compile( r'\s+' )
_syntax_peek_line = re.compile( r'(.*)$', re.MULTILINE )

class Source(object):
	def __init__(self, text):
		#FEATURE: normalize text line-endings
		
		self._text = text
		self._at = 0
		self._size = len(text)

	def skip_space(self):
		self.match( _syntax_skip_space )
	
	def is_at_end(self):
		return self._at >= self._size
		
	def peek_line(self):
		m = _syntax_peek_line.match( self._text, self._at )
		if m == None:
			return ""
		return m.group(1)
		
	def peek_char(self):
		return self._text[self._at]
		
	def next_char(self):
		c = self._text[self._at]
		self._at += 1
		return c
		
	def match( self, re ):
		m = re.match( self._text, self._at )
		if m != None:
			self._at = m.end()
		return m
		
	def peek_match( self, re ):
		m = re.match( self._text, self._at )
		return m
		
	def to_match( self, re ):
		m = re.search( self._text, self._at )
		if m != None:
			text = self._text[self._at:m.start()]
			self._at = m.end()
			return m, text
		return None, None
	
	def map_position(self, where : int) -> Tuple[int,int]:
		lines = self._text.count( '\n', 0, self._at )
		last_line = self._text.rfind( '\n', 0, self._at )
		return ( lines, self._at - last_line )
		
	@property
	def position(self) -> int:
		return self._at
		
		
# Parses a file
# @param filename The name of the file to parse
# @return A node representing the document
def parse_file( filename ):
	in_file = open( filename, 'r', encoding = 'utf-8' )
	in_text = in_file.read()
	in_source = Source(in_text)
	
	root = Node(NodeType.container)
	_parse_container( root, in_source, '' )
	return root

	
_syntax_empty_line = re.compile( r'[\p{Space_Separator}\t]*$', re.MULTILINE )
_syntax_lead_space = re.compile( r'([\p{Space_Separator}\t]*)' )
_syntax_line = re.compile( r'(?!//)(#+|-|/)' )
_syntax_block = re.compile( r'(>|>>|//|\^([\p{L}\p{N}]*))\s*' )
_syntax_tag = re.compile( r'{%\s+(\p{L}+)\s' )
_syntax_raw = re.compile( r'(```)' )
_syntax_raw_end = re.compile( r'(^```)', re.MULTILINE )
_syntax_matter = re.compile( r'(^\+\+\+)') 
_syntax_matter_end = re.compile( r'(^\+\+\+$)', re.MULTILINE )
_syntax_annotation = re.compile( r'@(\p{L}+)' )
_syntax_rest_line = re.compile( r'(.*)$', re.MULTILINE )

# A feature may have any regex opening match, but requires a single character terminal
class FeatureParse(object):
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
	
_syntax_feature = re.compile(r'([\*_\[\(`\:])')
_syntax_feature_map = {
	'*': FeatureParse.open_close('*','*'),
	'_': FeatureParse.open_close('_','_'),
	'`': FeatureParse.raw('`','`'),
	'[': FeatureParse.open_close('[',']'),
	'(': FeatureParse.raw('(',')'),
}
_syntax_inline_note = re.compile( r'\^([\p{L}\p{N}]*)' )

def _parse_container( root, src, indent ):
	annotations = []
	blocks = []

	def append_block( block ):
		nonlocal annotations
		
		block.add_annotations( annotations )
		annotations = []
		blocks.append( block )
		
	while not src.is_at_end():
		if src.match( _syntax_empty_line ) != None:
			# TODO: it's unclear why this is needed, the regex doesn't consume the line end it appears.
			src.next_char()
			continue
			
		lead_space = src.peek_match( _syntax_lead_space ).group(1)
		if lead_space != indent:
			# TODO: add some strong rules about what's allowed here
			if len(lead_space) < len(indent):
				break
			if len(lead_space) > len(indent):
				assert len(blocks) > 0
				child_container = blocks[-1]
				child_container.promote_to_container()
				_parse_container( child_container, src, lead_space )
				
			continue
			
		_ = src.match( _syntax_lead_space )
		
		annotation_match = src.match( _syntax_annotation )
		if annotation_match != None:
			annotations.append( Annotation( annotation_match.group(1) ) )
			continue
			
		line_match = src.match( _syntax_line )
		if line_match != None:
			class_ = line_match.group(1)
			line = Node(NodeType.block)
			line.class_ = class_
			line.add_subs( _parse_line(src) )
			
			if class_ == '/':
				annotations.append( Annotation( 'comment', line) )
			else:
				append_block( line )
			continue
			
		tag = src.match( _syntax_tag )
		if tag != None:
			para = Node(NodeType.block)
			para.class_ = tag.group(1)
			while True:
				arg, end = _parse_string( src, '}' )
				if end: 
					break
				if arg is not None:
					para.add_arg( arg )
				
			append_block( para )
			continue
			
			
		block = src.match( _syntax_block )
		if block != None:
			class_ = block.group(1)
			para = _parse_para(src, indent)
			if class_ == '//':
				annotations.append( Annotation( 'comment', para ) )
			else:
				para.class_ = block.group(1)
				
				# TODO: howto match two groups with a dpeendent group to avoid this?
				if class_[0:1] == '^':
					para.class_ = '^'
					para.text = block.group(2)
				append_block( para )
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
			append_block( raw )
			continue
			
		matter_match = src.match( _syntax_matter )
		if matter_match != None:
			matter = Node(NodeType.matter)
			# TODO: parse data, matter.data = yaml-like parsing
			end_match, raw_text = src.to_match(_syntax_matter_end)
			assert end_match != None
			matter.text = raw_text
			append_block( matter )
			continue
			
			
		para = _parse_para(src, indent)
		# drop empty paragraphs
		if not para.sub_is_empty():
			append_block( para )


	root.add_subs( blocks )
	

def _expand_false_node(node):
	assert len(node.text) == 0
	sub = []
	
	open_bit = Node( NodeType.text )
	open_bit.text = node.class_
	sub.append( open_bit )
			
	sub.extend( node.iter_sub() )
	
	close_bit = Node( NodeType.text )
	close_bit.text = _syntax_feature_map[node.class_]
	sub.append( close_bit )
	return sub
	
	
def _parse_line( src : Source, terminal : str = '\n' ) -> Sequence[Node]:
	bits : List[Node] = []
	text = ''
	
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
		first = bits[at] if len(bits) > 0 else None
		while first is not None and first.class_ == ':':
			at += 1
			
		collect = bits[at:]
		bits = bits[:at]
		header = Node(NodeType.inline)
		header.class_ = ':'
		header.add_subs( collect )
		push_bit( header )
		
	def end_bits():
		pass
			
	while not src.is_at_end():
		c = src.peek_char()
		if c == terminal:
			_ = src.next_char()
			break
			
		if c == '\\':
			_ = src.next_char()
			text += src.next_char()
			continue
			
		note_match = src.match( _syntax_inline_note )
		if note_match != None:
			note_name = note_match.group(1)
			end_text()
			note = Node( NodeType.inline )
			note.class_ = '^'
			note.text = note_name
			push_bit( note )
			continue
			
		feature_match = src.match( _syntax_feature )
		if feature_match != None:
			feature_class = feature_match.group(1)
			end_text()
			
			if feature_class == ':':
				mark_header()
				continue
			
			feature_parse = _syntax_feature_map[feature_class]
			
			feature = Node( NodeType.inline )
			feature.class_ = feature_class
			if feature_parse.is_raw:
				feature_text = _parse_raw_escape_to( src, feature_parse.close_char )
				feature.text = feature_text
			else:
				feature_line = _parse_line( src, feature_parse.close_char )
				feature.add_subs( feature_line )
			push_bit( feature )
			continue
			
			
		text += src.next_char()
			
	end_text()
	end_bits()
	return bits

def _parse_raw_escape_to( src, close_char ):
	start = src.position
	text = ''
	
	while not src.is_at_end():
		c = src.next_char()
		if c == '\\':
			c = src.next_char()
		elif c == close_char:
			return text
		
		text += c
		
	raise Exception( f"{src.map_position(start)} Unclosed raw text feature {close_char}" )


def _parse_string( src, close_char : str ) -> Tuple[Optional[str], bool]:
	text = ''
	
	src.skip_space()
	has = False
	end = False
	while not src.is_at_end():
		c = src.next_char()
		if c == '\\':
			c = src.next_char()
			has = True
		elif c == close_char:
			end = True
			break
		elif _syntax_skip_space.search( c ) != None:
			break
		else:
			text += c
			has = True
			
	return (text if has else None, end)
		
	
def _parse_para( src, indent ):
	para = Node(NodeType.block)
	first = True
	while not src.is_at_end():
	
		# Parse Container preconsumes the leading space on the first entry to the paragraph, in order to do
		# other block matching. It's not sure how this can be avoided.
		if not first:
			lead_space = src.peek_match( _syntax_lead_space ).group(1)
			if lead_space != indent:
				break
			_ = src.match( _syntax_lead_space )
		first = False
			
		line = _parse_line(src)
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
	
"""
	Debugging and test compliance utitlity.
"""
class _dumper:
	def __init__(self, ansi = False):
		self.ansi = ansi
		
	def get( self, node : Node, indent : str = '' ) -> str:
		text = indent
		header = node.type.name
		if len(node.class_) > 0:
			header += '/' + node.class_
		text += self._bold(header)
		text += ' ' + node.text
		if node.has_args():
			text += "["
			text += ",".join( node.get_args() )
			text += "]"
		
		if node.has_annotations():
			for anno in node.iter_annotations():
				text += '\n{}\t@{}'.format( indent, self._alt(anno.class_) )
				if anno.node != None:
					text += '\n' + self.get( anno.node, indent + '\t\t' )
		if node.has_attr():
			text += '\n' + indent + '\tattrs\n'
			for attr in node.iter_attr():
				text += self.get( attr, indent + '\t\t' )
		else:
			text += '\n'
					
		indent += "\t"
		for sub in node.iter_sub():
			text += self.get( sub, indent )

		return text

	def _bold(self, text : str) -> str:
		if not self.ansi:
			return text
		return '\x1b[1m{}\x1b[m'.format(text)

	def _alt(self, text : str) -> str:
		if not self.ansi:
			return text
		return '\x1b[96m{}\x1b[m'.format(text)
		
		
def dump( node : Node ) -> None:
	print( _dumper( ansi = True ).get( node ) )
	
def get_dump( node : Node ) -> str:
	return _dumper().get( node )
