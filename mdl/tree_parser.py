# Tree parsing
import regex as re
from enum import Enum

class NodeType(Enum):
	# may contain blocks as children
	container = 1
	# may contain text and inline as children
	block = 2
	# text nodes may not have children
	text = 3
	# may contain text and inline as children
	inline = 4
	# may not contain children, text is the raw text
	raw = 5
	
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
		
	def add_sub( self, sub ):
		if self._type == NodeType.text:
			raise Exception( "The text type should not have children" )
		if self._type == NodeType.container and not sub._type in [NodeType.block, NodeType.raw]:
			raise Exception( "containers can only contain blocks/raw" )
		if self._type in [NodeType.block, NodeType.inline] and not sub._type in [NodeType.inline, NodeType.text]:
			raise Exception( "blocks/inlines can only contain inline/text" )
			
		assert isinstance(sub, Node)
		self._sub.append( sub )
		
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
		
	def add_subs( self, subs ):
		for sub in subs:
			self.add_sub( sub )
			
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
		
class Source(object):
	def __init__(self, text):
		#FEATURE: normalize text line-endings
		
		self._text = text
		self._at = 0
		self._size = len(text)
		
	def skip_space(self):
		pass
		
	def is_at_end(self):
		return self._at >= self._size
		
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
		
	def to_match( self, re ):
		m = re.search( self._text, self._at )
		if m != None:
			text = self._text[self._at:m.start()]
			self._at = m.end()
			return m, text
		return None, None
		
		
# Parses a file
# @param filename The name of the file to parse
# @return A node representing the document
def parse_file( filename ):
	in_file = open( filename, 'r', encoding = 'utf-8' )
	in_text = in_file.read()
	in_source = Source(in_text)
	
	root = Node(NodeType.container)
	root.add_subs( _parse_blocks( in_source ) )
	
	return root

_syntax_line = re.compile( '(?!//)(#+|---|/)' )
_syntax_block = re.compile( '(>|>>|//|\^([\p{L}\p{N}]*))' )
_syntax_raw = re.compile( '(```)' )
_syntax_annotation = re.compile( '@(\p{L}+)' )

# A feature may have any regex opening match, but requires a single character terminal
_syntax_feature = re.compile('([\*_\[\(])')
_syntax_feature_map = {
	'*': '*',
	'_': '_',
	'[': ']',
	'(': ')',
}
_syntax_inline_note = re.compile( '\^([\p{L}\p{N}]*)' )

def _parse_blocks( src ):
	nodes = []
	annotations = []

	def append_block( block ):
		nonlocal annotations
		
		block.add_annotations( annotations )
		annotations = []
		nodes.append( block )
		
	while not src.is_at_end():
		c = src.peek_char()
		
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
			
		block = src.match( _syntax_block )
		if block != None:
			class_ = block.group(1)
			para = _parse_para(src)
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
			end_match, raw_text = src.to_match(_syntax_raw)
			assert end_match != None
			raw.text = raw_text
			append_block( raw )
			continue
			
			
		para = _parse_para(src)
		# drop empty paragraphs
		if not para.sub_is_empty():
			append_block( para )
			
	return nodes
	

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
	
	
def _parse_line( src, terminal = '\n' ):
	bits = []
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
		# check for compound bits
		trail_bit = bit.type == NodeType.inline and bit.class_ == '('
			
		if len(bits) > 0 and bits[-1].type == NodeType.inline and bits[-1].class_ == '[' and not bits[-1].has_attr():
			# not continued, then collapse the bit to normal text
			# FEATURE: cleaner collapse
			if trail_bit:
				bits[-1].add_attr( bit )
				return
			else:
				push_bits( _expand_false_node( bits.pop() ) )
				
		elif trail_bit:
			push_bits( _expand_false_node( bit ) )
			return
			
			
		if bit.type == NodeType.text and len(bits) > 0 and bits[-1].type == NodeType.text:
			bits[-1].text += bit.text
		else:
			bits.append(bit)
		
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
			feature_line = _parse_line( src, _syntax_feature_map[feature_class] )
			feature = Node( NodeType.inline )
			feature.class_ = feature_class
			feature.add_subs( feature_line )
			push_bit( feature )
			continue
			
			
		text += src.next_char()
			
	end_text()
	end_bits()
	return bits


def _parse_para( src ):
	para = Node(NodeType.block)
	while not src.is_at_end():
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
	
# Rough debugging utility
def dump( node, indent = '' ):
	print( _dump_get( node, indent ) )

def _dump_get( node, indent = '' ):
	text = indent
	header = node.type.name
	if len(node.class_) > 0:
		header += '/' + node.class_
	text += _bold(header)
	text += ' ' + node.text
	if node.has_annotations():
		for anno in node.iter_annotations():
			text += '\n{}\t@{}'.format( indent, _alt(anno.class_) )
			if anno.node != None:
				text += '\n' + _dump_get( anno.node, indent + '\t\t' )
	if node.has_attr():
		text += '\n' + indent + '\tattrs\n'
		for attr in node.iter_attr():
			text += _dump_get( attr, indent + '\t\t' )
	else:
		text += '\n'
				
	indent += "\t"
	for sub in node.iter_sub():
		text += _dump_get( sub, indent )

	return text

def _bold(text):
	return '\x1b[1m{}\x1b[m'.format(text)

def _alt(text):
	return '\x1b[96m{}\x1b[m'.format(text)
