# Abstract document tree (the document equivalent of an abstract syntax tree)

"""
Base node types form the doc type tree. They should not be instantiated.
"""
import typing

class BlockNode(object):
	pass
	
class BaseBlock(BlockNode):
	def __init__(self, subs : typing.List['BlockNode'] = []):
		self._sub : typing.List['BlockNode'] = []
		self.add_subs( subs )

	def _validate_sub( self, sub : BlockNode ) -> None:
		assert isinstance( sub, BlockNode ), sub
	
	def add_sub( self, sub : BlockNode ) -> None:
		self._validate_sub( sub )
		self._sub.append( sub )
		
	def add_subs( self, subs : typing.List['BlockNode'] ) -> None:
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ):
		return self._sub

		
class ParagraphElement(object):
	def __init__(self, subs = []):
		self._sub : typing.List['ParagraphElement'] = []
		self.add_subs( subs )
		
	def _validate_sub( self, sub ):
		assert isinstance( sub, ParagraphElement ), sub
		
	def add_sub( self, sub : 'ParagraphElement' ):
		self._validate_sub( sub )
		self._sub.append( sub )
		
	def add_subs( self, subs : typing.List['ParagraphElement'] ) -> None:
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ):
		return self._sub
		
		
class Paragraph(BlockNode):
	def __init__(self, subs = []):
		self._sub : typing.List[ParagraphElement] = []
		self.add_subs( subs )
		
	def _validate_sub( self, sub ):
		assert isinstance( sub, ParagraphElement ), sub
		
	def add_sub( self, sub : ParagraphElement  ):
		self._validate_sub( sub )
		self._sub.append( sub )
		
	def add_subs( self, subs : typing.List['ParagraphElement'] ) -> None:
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ):
		return self._sub
		
		
		
# TODO: these "Empty" names are yucky
class BaseInlineEmpty(object):
	def __init__(self):
		pass

class BaseBlockEmpty(object):
	def __init__(self):
		pass
		
"""
Leaf types may only inherit from Base node types. This prevents collision on simple visitors, as well as keeping the "is-a" relationships clean.
"""
class Block(BaseBlock):
	def __init__(self, class_, subs = []):
		super().__init__( subs )
		self._class_ = class_
		
	@property
	def class_(self):
		return self._class_
		
		
class BlockClass(object):
	def __init__(self, name):
		self.name = name
		
block_quote = BlockClass('quote')
block_blurb = BlockClass('blurb')
block_aside = BlockClass('aside')
		
		
class Text(ParagraphElement):
	def __init__(self, text):
		self.text = text
		
class Inline(ParagraphElement):
	def __init__(self, feature):
		super().__init__()
		assert isinstance(feature, InlineFeature)
		self.feature = feature
		
class Section(BaseBlock):
	def __init__(self, level, title_text_block = None ):
		super().__init__()
		self.title = title_text_block
		self.level = level

class List(BaseBlock):
	def __init__(self):
		super().__init__()
		
	def _validate_sub( self, sub ):
		super()._validate_sub( sub )
		assert isinstance( sub, ListItem )

class ListItem(BaseBlock):
	def __init__(self):
		super().__init__()
		
class InlineFeature(object):
	def __init__(self, name):
		self.name = name
		
feature_bold = InlineFeature("bold")
feature_italic = InlineFeature("italic")
feature_code = InlineFeature("code")

class Link(ParagraphElement):
	def __init__(self, url):
		super().__init__()
		self.url = url
		
class Note(BaseInlineEmpty):
	def __init__(self, node):
		super().__init__()
		self.node = node
		
class Code(BaseBlockEmpty):
	def __init__(self, text, class_):
		super().__init__()
		self.text = text
		self.class_ = class_
	
