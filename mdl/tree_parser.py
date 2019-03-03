# Tree parsing
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
		pass
		
	def add_sub( self, sub ):
		assert isinstance(sub, Node)
		self._sub.append( sub )
		
	def add_subs( self, subs ):
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ):
		return iter( self._sub )
		
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

class Source(object):
	def __init__(self, text):
		#FEATURE: normalize text line-endings
		
		self.text = text
		self.at = 0
		self.size = len(text)
		
	def skip_space(self):
		pass
		
	def is_at_end(self):
		return self.at >= self.size
		
	def peek_char(self):
		return self.text[self.at]
		
	def next_char(self):
		c = self.text[self.at]
		self.at += 1
		return c
		
		
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

def _parse_blocks( src ):
	nodes = []
	
	while not src.is_at_end():
		c = src.peek_char()
		
		if c == '#':
			_ = src.next_char()
			
			line = Node(NodeType.head)
			line.add_subs( _parse_line(src) )
			nodes.append( line )
		else:
			para = _parse_para(src)
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
		
	return para
	
# Rough debugging utility
def dump( node, indent = '' ):
	print( "{}({}) {}".format( indent, node.type, node.text ) )
	indent += "\t"
	
	for sub in node.iter_sub():
		dump( sub, indent )


	
