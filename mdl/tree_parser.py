# Tree parsing
import re
from enum import Enum

class NodeType(Enum):
	root = 1
	head = 2
	para = 3
	text = 4
	
class Node(object):
	def __init__(self, type):
		self._sub = []
		self._text = None
		self._type = type
		self._class_ = None
		pass
		
	def add_sub( self, sub ):
		assert isinstance(sub, Node)
		self._sub.append( sub )
		
	def add_subs( self, subs ):
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ):
		return iter( self._sub )
		
	def sub_is_empty( self ):
		return len(self._sub) == 0
		
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
		
		
		
# Parses a file
# @param filename The name of the file to parse
# @return A node representing the document
def parse_file( filename ):
	in_file = open( filename, 'r', encoding = 'utf-8' )
	in_text = in_file.read()
	in_source = Source(in_text)
	
	root = Node(NodeType.root)
	root.add_subs( _parse_blocks( in_source ) )
	
	return root

_syntax_head = re.compile('(#+)')

def _parse_blocks( src ):
	nodes = []
	
	while not src.is_at_end():
		c = src.peek_char()
		
		head = src.match( _syntax_head )
		if head != None:
			_ = src.next_char()
			
			line = Node(NodeType.head)
			line.class_ = head.group(1)
			line.add_subs( _parse_line(src) )
			nodes.append( line )
		else:
			para = _parse_para(src)
			if para != None:
				nodes.append( para )
			
	return nodes
	

def _parse_line( src ):
	text = ''
	while not src.is_at_end():
		c = src.next_char()
		if c == '\n':
			break
		else:
			text += c
			
	#FEATURE: white space stripping and collapsing
	if len(text) == 0:
		return []
	
	n = Node(NodeType.text)
	n.text = text
	return [n]

def _parse_para( src ):
	para = Node(NodeType.para)
	while not src.is_at_end():
		line = _parse_line(src)
		if len(line) == 0:
			break
		para.add_subs( line )
		
	if para.sub_is_empty():
		return None
		
	return para
	
# Rough debugging utility
def dump( node, indent = '' ):
	print( "{}({}/{}) {}".format( indent, node.type, node.class_, node.text ) )
	indent += "\t"
	
	for sub in node.iter_sub():
		dump( sub, indent )


	
