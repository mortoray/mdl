# Tree parsing
from __future__ import annotations #type: ignore
from typing import *

from enum import Enum

class NodeType(Enum):
	# may contain blocks and containers as children
	container = 1
	# may contain text and inline as children
	block = 2
	# text nodes may not have children
	text = 3
	# may contain text and inline as children
	inline = 4
	# may not contain children, text is the raw text
	raw = 5
	# may not contain children, data is the structured data
	matter = 6
	
class Annotation(object):
	def __init__(self, class_, node = None):
		self._class_ = class_
		self._node = node
		
	@property
	def class_( self ):
		return self._class_
		
	@property
	def node( self ):
		return self._node
		
class Node(object):
	def __init__(self, type):
		self._sub = []
		self._text = ''
		self._type = type
		self._class_ = ''
		self._attr = None
		self._annotations = None
		self._args = []
		self._data = None
		
	def __str__( self ):
		return "{}@{} \"{}\"".format( self._type, self._class_, self._text )
		
	def validate_sub( self, sub ):
		if self._type == NodeType.text:
			raise Exception( "The text type should not have children" )
		if self._type == NodeType.container and not sub._type in [NodeType.block, NodeType.raw, NodeType.container, NodeType.matter]:
			raise Exception( "containers can only contain blocks/raw" )
		if self._type in [NodeType.block, NodeType.inline] and not sub._type in [NodeType.inline, NodeType.text]:
			raise Exception( "blocks/inlines can only contain inline/text" )
			
		assert isinstance(sub, Node)
		
	def add_annotations( self, annotations ):
		if len(annotations) == 0:
			return
		if self._annotations == None:
			self._annotations = []
		self._annotations += annotations[:]
		
	def get_annotation( self, class_ ):
		if self._annotations == None:
			return None
		for anno in self._annotations:	
			if anno.class_ == class_:
				return anno
		return None
		
	def add_arg( self, arg : str):
		self._args.append( arg )
		
	def get_args( self ) -> List[str]:
		return self._args[:]
		
	def has_args( self ) -> bool:
		return len(self._args) > 0
		
	def promote_to_container( self ) -> None:
		first_child = Node( self._type )
		first_child._text = self._text
		self._text = ''

		first_child._sub = self._sub
		self._sub = [first_child]
		
		self._type = NodeType.container
		
	def remove_sub_at( self, index : int ) -> None:
		del self._sub[index]
		
	"""
		Splits this container node at the index, keeping children before the index in this container and those after in the returned container.
	"""
	def split_at( self, index : int ) -> Node:
		container = Node( self._type )
		container._sub = self._sub[index:]
		self._sub = self._sub[:index]
		return container
		
	def add_subs( self, subs : Sequence[Node] ) -> None:
		for sub in subs:
			self.add_sub( sub )
			
	def add_sub( self, sub : Node ) -> None:
		self.validate_sub( sub )
		self._sub.append( sub )
			
	# As Python lacks a random access iterator, this returns a list view of the subs, it should not be modified
	def iter_sub( self ):
		return self._sub
		
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
		
	def add_attr( self, node ):
		if self._attr == None:
			self._attr = []
		self._attr.append(node)
		
	def has_attr( self ):
		return self._attr != None and len(self._attr) > 0
		
	def iter_attr( self ):
		return iter(self._attr)
		
	def get_attrs(self):
		if self._attr == None:
			return []
		return self._attr
		
	def has_annotations( self ):
		return self._annotations != None and len(self._annotations) > 0
		
	def iter_annotations( self ):
		return iter( self._annotations )
