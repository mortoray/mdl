# Abstract document tree (the document equivalent of an abstract syntax tree)

"""
Base node types form the doc type tree. They should not be instantiated.
"""
from __future__ import annotations # type: ignore

import typing
from enum import Enum

T = typing.TypeVar('T')
class NodeContainer(typing.Generic[T]):
	def __init__(self):
		super().__init__()
		self._sub : typing.List[T] = []

	def _validate_sub( self, sub : T ) -> None:
		# There is no way to check if sub is of type T here :/
		pass
	
	def add_sub( self, sub : T ) -> None:
		self._validate_sub( sub )
		self._sub.append( sub )
		
	def add_subs( self, subs : typing.Sequence[T] ) -> None:
		for sub in subs:
			self.add_sub( sub )
			
	def iter_sub( self ) -> typing.Sequence[T]:
		return self._sub
		
	def len_sub( self ) -> int:
		return len(self._sub)
		
	def first_sub( self ) -> T:
		return self._sub[0]
		

class BlockNode:
	def __init__(self):
		super().__init__()
	
class BaseBlock(BlockNode, NodeContainer[BlockNode]):
	def __init__(self, subs : typing.List[BlockNode] = []):
		super().__init__()
		self.add_subs( subs )

	def _validate_sub( self, sub : BlockNode ) -> None:
		assert isinstance( sub, BlockNode ), sub

		
class Element:
	def __init__(self):
		super().__init__()
		
class ElementContainer(NodeContainer[Element]):
	def __init__(self):
		super().__init__()

	def _validate_sub( self, sub : Element ) -> None:
		assert isinstance( sub, Element ), sub
		
class ParagraphElement(Element,ElementContainer):
	def __init__(self, subs : typing.List[Element] = []):
		super().__init__()
		self.add_subs( subs )
		
class Paragraph(BlockNode, ElementContainer):
	def __init__(self, subs = []):
		super().__init__()
		self.add_subs( subs )
		
		
class BaseBlockEmpty(BlockNode):
	def __init__(self):
		super().__init__()
		
"""
Leaf types may only inherit from Base node types. This prevents collision on simple visitors, as well as keeping the "is-a" relationships clean.
"""
class Block(BaseBlock):
	def __init__(self, class_ : BlockClass, subs = []):
		super().__init__( subs )
		self._class_ = class_
		
	@property
	def class_(self) -> BlockClass:
		return self._class_
		
		
class BlockClass(object):
	def __init__(self, name):
		self.name = name
		
block_quote = BlockClass('quote')
block_blurb = BlockClass('blurb')
block_aside = BlockClass('aside')
		
		
class Text(Element):
	def __init__(self, text):
		super().__init__()
		self.text = text
		
class Inline(ParagraphElement):
	def __init__(self, feature : InlineFeature):
		super().__init__()
		assert isinstance(feature, InlineFeature)
		self.feature = feature
		
class Section(BaseBlock):
	def __init__(self, level, title_text_block : typing.Optional[typing.List[BaseBlock]] = None ):
		super().__init__()
		self.title = title_text_block
		self.level = level
	

class ListItem(BaseBlock):
	def __init__(self):
		super().__init__()

class List(BlockNode, NodeContainer[ListItem]):
	def _validate_sub( self, sub : ListItem ) -> None:
		assert isinstance( sub, ListItem ), sub

		
class InlineFeature(object):
	def __init__(self, name : str):
		self.name = name
		
feature_bold = InlineFeature("bold")
feature_italic = InlineFeature("italic")
feature_code = InlineFeature("code")

class Link(ParagraphElement):
	def __init__(self, url : str):
		super().__init__()
		self.url = url
		

class Note(ParagraphElement):
	def __init__(self, elements : typing.Sequence[Element] = []):
		super().__init__()
		self.add_subs( elements )
		
class Code(BaseBlockEmpty):
	def __init__(self, text : str, class_ : str):
		super().__init__()
		self.text = text
		self.class_ = class_
	

class EmbedClass(Enum):
	image = 1
	
class Embed(BaseBlockEmpty):
	def __init__(self, class_ : EmbedClass, url : str ):
		super().__init__()
		self.class_ = class_
		self.url = url
		
