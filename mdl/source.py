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
		
	def line_context(self) -> str:
		start = self.offset
		back_lines = 2
		while start > 0:
			c = self.source._text[start]
			if c == '\n':
				back_lines -=1
				if back_lines == 0:
					# don't start with linefeed
					start += 1
					break
			start -=1
			
		end = start
		lines = 4
		while end < len(self.source._text):
			c = self.source._text[end]
			if c == '\n':
				lines -=1
				if lines == 0:
					break
			end += 1

		return self.source._text[start:end]
		
	def line_at(self) -> int:
		# TODO: This is still broken for MCL files embedded documents
		# It's unclear why base_offset was removed before, if it's one file we want relative
		# to the entire file. If it's a section, yes, we'd like to know the relative offset in 
		# some cases, but this is usually for visual output, so uncertain...
		# q = min(self.offset + self.source._base_offset, len(self.source._text)-self.source._base_offset)
		q = min(self.offset, len(self.source._text))
		line = 1
		while q > 1:
			q -= 1
			c = self.source._text[q]
			if c == '\n':
				line += 1
				
		return line
	
	def col_at(self, tab_size = 4) -> int:
		# q = min(self.offset + self.source._base_offset, len(self.source._text)-self.source._base_offset)
		q = min(self.offset, len(self.source._text))
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
		
	def skip_empty_lines(self) -> int:
		"""
			Skips empty lines in the input, returning the count of the skipped lines.
		"""
		skipped = 0
		while not self.is_at_end():
			m = _syntax_empty_line.match( self._text, self._at )
			if m == None:
				break
			skipped += 1
			self._at = m.end()
			self.match( _syntax_line_ends )
			
		return skipped
	
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
		"""
			Checks for a matching indent and removes it from the input if it matches.
			
			@return 
				[0] True is indent matches provided indent string
				[1] the actual leading space
		"""
		lead_space = self.peek_match( _syntax_lead_space ).group(1)
		if lead_space != indent:
			return (False, lead_space)
		_ = self.match( _syntax_lead_space )
		return (True, lead_space)
		
	def exceed_indent(self, indent: str) -> Tuple[bool, str]:
		"""
			@return
				[0] True if the lead space matches and exceeds the provided indent
				[1] the actual leading space
		"""
		lead_space = self.peek_match( _syntax_lead_space ).group(1)
		if len(lead_space) < len(indent):
			return (False, lead_space)
		if lead_space[:len(indent)] != indent:
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
		
	def restore_location(self, location: SourceLocation) -> None:
		assert location.source == self
		self._at = location.offset
		
	def fail(self, code: str, *message) -> NoReturn:
		self.fail_from(self.location, code, *message)
		
	def fail_from(self, location: SourceLocation, code: str, *message) -> NoReturn:
		raise ParseException(code=code, location=location, message=list(message))
	
class ParseException(Exception):
	def __init__(self, *, code: str, location: SourceLocation, message: list[str]=[]) -> None:
		self._code = code
		self._location = location
		self._message = message
		
		loc = location.translate()
		msg = f'{loc[0]}:{loc[1]},{loc[2]}:{":".join([code] + message)}'
		super().__init__(msg)

			
	@property
	def code(self) -> str:
		return self._code
		
	def get_context(self) -> str:
		line_prefix = ' | '
		text = self._location.line_context().splitlines()
		return "\n".join( line_prefix + line for line in text )
		
		
	def format_line(self) -> str:
		loc = self._location.translate()
		msg = f'{loc[0]}:{loc[1]},{loc[2]}:{":".join([self._code] + self._message)}'
		return msg
		
