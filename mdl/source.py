from typing import *
import regex as re #type: ignore

_syntax_skip_space = re.compile( r'\s+' )
_syntax_peek_line = re.compile( r'(.*)$', re.MULTILINE )
_syntax_lead_space = re.compile( r'([\p{Space_Separator}\t]*)' )
_syntax_empty_line = re.compile( r'[\p{Space_Separator}\t]*$', re.MULTILINE )
_syntax_line_ends = re.compile( r'[\n\r]' )

class Source(object):
	def __init__(self, text):
		#FEATURE: normalize text line-endings
		
		self._text = text
		self._at = 0
		self._size = len(text)

	def skip_space(self):
		self.match( _syntax_skip_space )
		
	def skip_empty_lines(self) -> None:
		while not self.is_at_end():
			m = _syntax_empty_line.match( self._text, self._at )
			if m == None:
				return
			self._at = m.end()
			self.match( _syntax_line_ends )
	
	def is_at_end(self):
		return self._at >= self._size
		
	def match_line(self):
		m = _syntax_peek_line.match( self._text, self._at )
		if m == None:
			return ""
		self._at = m.end()
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

	def match_indent(self, indent : str) -> Tuple[bool, str]:
		lead_space = self.peek_match( _syntax_lead_space ).group(1)
		if lead_space != indent:
			return (False, lead_space)
		_ = self.match( _syntax_lead_space )
		return (True, lead_space)
		
		
	def parse_token( self, exclude : List[str] ) -> str:
		text = ''
		while not self.is_at_end():
			c = self.peek_char()
			if _syntax_skip_space.match(c) or c in exclude:
				break
			text += self.next_char()
			
		return text
		

__all__ = [ 'Source' ]
