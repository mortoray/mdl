__all__ = [ 'Source', 'SourceLocation' ]

from typing import *
import regex as re #type: ignore
import sys

re.DEFAULT_VERSION = re.VERSION1

_syntax_skip_space = re.compile( r'\s+' )
_syntax_skip_nonline_space = re.compile( r'[\s--[\r\n]]+' )
_syntax_peek_line = re.compile( r'(.*)$', re.MULTILINE )
_syntax_lead_space = re.compile( r'([\p{Space_Separator}\t]*)' )
_syntax_empty_line = re.compile( r'[\p{Space_Separator}\t]*$', re.MULTILINE )
_syntax_line_ends = re.compile( r'[\n\r]' )


class SourceLocation(NamedTuple):
	source: 'Source'
	offset: int
	
	def translate(self, tab_size = 4) -> Tuple[Optional[str],int,int]:
		return (
			self.source._path,
			self.line_at(),
			self.col_at(tab_size)
		)
		
		
	def line_at(self) -> int:
		q = min(self.offset + self.source._base_offset, len(self.source._text)-self.source._base_offset)
		line = 1
		while q > 1:
			q -= 1
			c = self.source._text[q]
			if c == '\n':
				line += 1
				
		return line
	
	def col_at(self, tab_size = 4) -> int:
		q = min(self.offset + self.source._base_offset, len(self.source._text)-self.source._base_offset)
		col = 1
		while q > 1:
			q -= 1
			c = self.source._text[q]
			if c == '\n':
				break
			if c == '\t':
				col += tab_size
			else:
				col += 1
		
		return col
		
	
class Source(object):
	class _private:
		pass
		
	def __init__(self, token: _private, text, base_offset : int = 0, path : Optional[str] = None ):
		#FEATURE: normalize text line-endings
		
		self._text = text
		self._at = 0
		self._size = len(text)
		self._path = path
		self._base_offset = base_offset

	@classmethod 
	def with_text( class_, text : str, base_location : Optional[SourceLocation] = None ) -> 'Source':
		src = Source(
			Source._private(), 
			text=text, 
			base_offset=base_location.offset if not base_location is None else 0,
			path=base_location.source._path if not base_location is None else None,
		)
		return src
		
	@classmethod
	def with_filename( class_, filename : str ) -> 'Source':
		in_file = open( filename, 'r', encoding = 'utf-8' )
		in_text = in_file.read()
		src = Source(Source._private(), in_text, path=filename)
		return src
		
	def skip_space(self):
		self.match( _syntax_skip_space )
		
	def skip_nonline_space(self):
		self.match( _syntax_skip_nonline_space )
		
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
		
	def parse_string( self, close_char : str ) -> str:
		text = ''
		
		while not self.is_at_end():
			c = self.next_char()
			if c == '\\':
				c = self.next_char()
				has = True
			elif c == close_char:
				break
			
			text += c
				
		return text

	def parse_string_to( self, *, 
		char : Optional[str] = None, consume_terminal : bool = False,
		re = None,
	) -> str:
		text = ''
		
		while not self.is_at_end():
			if consume_terminal:
				if re is not None:
					if self.match(re):
						break
				c = self.next_char()
				if c == char:
					break
					
			else:
				if re is not None:
					if self.peek_match(re):
						break
				c = self.peek_char()
				if c == char:
					break
					
				c = self.next_char()
				
			if c == '\\':
				c = self.next_char()
				has = True
			
			text += c
				
		return text
		
	
	@property
	def location(self) -> SourceLocation:
		return SourceLocation(self, self._at)
		
	def fail(self, *message) -> NoReturn:
		self.fail_from(self.location, *message)
		
	def fail_from(self, location: SourceLocation, *message) -> NoReturn:
		loc = location.translate()
		msg = f'{loc[0]}:{loc[1]},{loc[2]}:{":".join(message)}'
		print( msg, file=sys.stderr )
		raise Exception(msg)
	
