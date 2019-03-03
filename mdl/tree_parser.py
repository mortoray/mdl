# Tree parsing
import re
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
	
class Node(object):
	def __init__(self, type):
		self._sub = []
		self._text = None
		self._type = type
		self._class_ = None
		pass
		
	def add_sub( self, sub ):
		if self._type == NodeType.text:
			raise Exception( "The text type should not have children" )
		if self._type == NodeType.container and not sub._type in [NodeType.block, NodeType.raw]:
			raise Exception( "containers can only contain blocks/raw" )
		if self._type in [NodeType.block, NodeType.inline] and not sub._type in [NodeType.inline, NodeType.text]:
			raise Exception( "blocks/inlines can only contain inline/text" )
			
		assert isinstance(sub, Node)
		self._sub.append( sub )
		
		
	def add_subs( self, subs ):
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ):
		return iter( self._sub )
		
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
			print ("!!!!", self._at, m.start())
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

_syntax_line = re.compile( '(#+|---)' )
_syntax_block = re.compile( '(>)' )
_syntax_raw = re.compile( '(```)' )

# A feature may have any regex opening match, but requires a single character terminal
_syntax_feature = re.compile('([\*_\[\(])')
_syntax_feature_map = {
	'*': '*',
	'_': '_',
	'[': ']',
	'(': ')',
}

def _parse_blocks( src ):
	nodes = []
	
	while not src.is_at_end():
		c = src.peek_char()
		
		line_match = src.match( _syntax_line )
		if line_match != None:
			line = Node(NodeType.block)
			line.class_ = line_match.group(1)
			line.add_subs( _parse_line(src) )
			nodes.append( line )
			continue
			
		block = src.match( _syntax_block )
		if block != None:
			para = _parse_para(src)
			para.class_ = block.group(1)
			nodes.append( para )
			continue
			
		raw_match = src.match( _syntax_raw )
		if raw_match != None:
			raw = Node(NodeType.raw)
			end_match, raw_text = src.to_match(_syntax_raw)
			assert end_match != None
			raw.text = raw_text
			nodes.append( raw )
			continue
			
			
		para = _parse_para(src)
		# drop empty paragraphs
		if not para.sub_is_empty():
			nodes.append( para )
			
	return nodes
	

def _parse_line( src, terminal = '\n' ):
	bits = []
	text = ''
	
	def end_text():
		nonlocal text
		if len(text) == 0:
			return
		
		n = Node(NodeType.text)
		n.text = text
		bits.append(n)
		text = ''
			
	while not src.is_at_end():
		c = src.peek_char()
		if c == terminal:
			_ = src.next_char()
			break
			
		if c == '\\':
			_ = src.next_char()
			text += src.next_char()
			continue
			
		feature_match = src.match( _syntax_feature )
		if feature_match != None:
			feature_class = feature_match.group(1)
			end_text()
			feature_line = _parse_line( src, _syntax_feature_map[feature_class] )
			feature = Node( NodeType.inline )
			feature.class_ = feature_class
			feature.add_subs( feature_line )
			bits.append( feature )
			continue
			
			
		text += src.next_char()
			
	end_text()
	return bits


def _parse_para( src ):
	para = Node(NodeType.block)
	while not src.is_at_end():
		line = _parse_line(src)
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
	print( "{}({}/{}) {}".format( indent, node.type.name, node.class_, node.text ) )
	indent += "\t"
	
	for sub in node.iter_sub():
		dump( sub, indent )
