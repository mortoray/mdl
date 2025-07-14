__all__ = ['TreeFormatter']

from typing import *
from enum import Enum, auto
import io

class TFType(Enum):
	section = auto()
	capture = auto()

TFPair = Tuple[TFType,Optional[str]]
TFCapture = Callable[[str],str]

class Context:
	def __init__(self):
		self.body = io.StringIO()
		self.post : List[TFPair] = []
		self.capture : Optional[TFCapture] = None
		self.indent : str | None = None
		
class TreeFormatter:
	def __init__(self):
		self._cur_context = Context()
		self._context : List[Context] = [ self._cur_context ]
		
	def section(self, open : str, close : Optional[str] ):
		self._cur_context.body.write( open )
		self._cur_context.post.append( (TFType.section, close) )
		
	#TODO: merge with end_context / remove
	def end_section(self):
		s = self._cur_context.post.pop()
		assert s[0] == TFType.section
		if s[1] is not None:
			self._cur_context.body.write( s[1] )
			
	def write( self, text : str ):
		self._cur_context.body.write( text )

	def open_context( self ):
		self._cur_context = Context()
		self._context.append( self._cur_context )
	
	def end_context( self ):
		ctx = self._context.pop()
		for item in ctx.post:
			if item[1] is not None:
				ctx.body.write(item[1])
				
		self._cur_context = self._context[-1]
		text = ctx.body.getvalue()
		if ctx.capture is not None:
			text = ctx.capture(text)
		self._cur_context.body.write( text )
		
	def set_indent( self, indent: str ): 
		self._context[-1].indent = indent
		
	def capture(self, render : Callable[[str],str]):
		assert self._cur_context.capture is None
		self._cur_context.capture = render
		
		
	@property
	def value(self) -> str:
		return self._cur_context.body.getvalue()
