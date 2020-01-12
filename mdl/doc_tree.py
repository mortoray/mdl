# Abstract document tree (the document equivalent of an abstract syntax tree)

"""
Base node types form the doc type tree. They should not be instantiated.
"""
from __future__ import annotations # type: ignore

import typing, abc
from enum import Enum


class VisitCallback(typing.Protocol):
	@abc.abstractmethod
	def enter(self, node : Node, segment : int ) -> bool:
		raise NotImplementedError
		
	@abc.abstractmethod
	def exit(self, node : Node, segment : int ) -> None:
		raise NotImplementedError
		
		
class StackVisitor:
	def __init__(self, proc : typing.Callable[[Node,typing.List[Node]], bool]):
		self.stack : typing.List[Node] = []
		self.proc = proc
		
	def enter( self, node : Node, segment : int ) -> bool:
		self.stack.append( node )
		return self.proc( node, self.stack )

	def exit( self, node : Node, segment : int ) -> None:
		self.stack.pop()
		

class Node(abc.ABC):
	def __init__(self):
		super().__init__()
		
	def visit( self, proc : VisitCallback ) -> None:
		proc.enter( self, 0 )
		proc.exit( self, 0 )
		
T = typing.TypeVar('T', bound = Node)
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
		
	def visit( self, proc : VisitCallback ) -> None:
		assert isinstance(self, Node)
		if proc.enter( self, 0 ):
			for node in self._sub:
				node.visit( proc )
				
		proc.exit( self, 0 )
			

class BlockNode(Node):
	def __init__(self):
		super().__init__()
	
class BlockContainer(NodeContainer[BlockNode], BlockNode):
	def __init__(self, subs : typing.List[Block] = []):
		super().__init__()
		self.add_subs( subs )

	def _validate_sub( self, sub : BlockNode ) -> None:
		assert isinstance( sub, BlockNode ), sub

		
class Element(Node):
	def __init__(self):
		super().__init__()
		
		
class ElementContainer(NodeContainer[Element]):
	def __init__(self):
		super().__init__()

	def _validate_sub( self, sub : Element ) -> None:
		assert isinstance( sub, Element ), sub
		
class ParagraphElement(ElementContainer, Element):
	def __init__(self, subs : typing.List[Element] = []):
		super().__init__()
		self.add_subs( subs )
		
class Paragraph(ElementContainer, BlockNode):
	def __init__(self, subs = []):
		super().__init__()
		self.add_subs( subs )
	
		
"""
Leaf types may only inherit from Base node types. This prevents collision on simple visitors, as well as keeping the "is-a" relationships clean.
"""
class Block(BlockContainer):
	def __init__(self, class_ : BlockClass, subs = []):
		super().__init__( subs )
		self._class_ = class_
		
	@property
	def class_(self) -> BlockClass:
		return self._class_
		
		
class BlockClass(object):
	def __init__(self, name):
		self.name = name
		
	def __str__(self) -> str:
		return self.name
		
block_quote = BlockClass('quote')
block_blurb = BlockClass('blurb')
block_aside = BlockClass('aside')
block_promote = BlockClass('promote')
		
		
class Text(Element):
	def __init__(self, text : str):
		super().__init__()
		self.text = text
	
		
class Inline(ParagraphElement):
	def __init__(self, feature : InlineFeature):
		super().__init__()
		assert isinstance(feature, InlineFeature)
		self.feature = feature
		
class Section(BlockContainer):
	def __init__(self, level, title_text_block : typing.Optional[typing.List[BlockContainer]] = None ):
		super().__init__()
		self.title = title_text_block
		self.level = level
		
	def visit( self, proc : VisitCallback ) -> None:
		if proc.enter( self, 0 ):
			if self.title is not None:
				if proc.enter( self, 1 ):
					for tnode in self.title:
						tnode.visit( proc )
				proc.exit( self, 1 )
					
			for node in self._sub:
				node.visit( proc )
				
		proc.exit( self, 0 )
	

class ListItem(BlockContainer):
	def __init__(self):
		super().__init__()

class List(NodeContainer[ListItem], BlockNode):
	def _validate_sub( self, sub : ListItem ) -> None:
		assert isinstance( sub, ListItem ), sub

		
class InlineFeature(object):
	def __init__(self, name : str):
		self.name = name

feature_none = InlineFeature("none")
feature_bold = InlineFeature("bold")
feature_italic = InlineFeature("italic")
feature_code = InlineFeature("code")
feature_header = InlineFeature("header")

class Link(ParagraphElement):
	def __init__(self, url : str, title : typing.Optional[str] = None ):
		super().__init__()
		self.url = url
		self.title = title
		

class Note(ParagraphElement):
	def __init__(self, elements : typing.Sequence[Element] = []):
		super().__init__()
		self.add_subs( elements )
		
class Token(ParagraphElement):
	def __init__(self, args : typing.List[str]):
		super().__init__()
		self.args = args
		
class Code(BlockNode):
	def __init__(self, text : str, class_ : str):
		super().__init__()
		self.text = text
		self.class_ = class_

class EmbedClass(Enum):
	image = 1
	abstract = 2
	
class Embed(BlockNode):
	def __init__(self, class_ : EmbedClass, url : str ):
		super().__init__()
		self.class_ = class_
		self.url = url
		
