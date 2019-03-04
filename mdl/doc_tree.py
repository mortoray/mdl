# Abstract document tree (the document equivalent of an abstract syntax tree)

"""
Base node types form the doc type tree. They should not be instantiated.
"""

class BaseBlock(object):
	def __init__(self):
		self.sub = []
		
class BaseInlineBlock(BaseBlock):
	def __init__(self):
		super().__init__()
		
		
"""
Leaf types may only inherit from Base node types. This prevents collision on simple visitors, as well as keeping the "is-a" relationships clean.
"""
class Block(BaseBlock):
	def __init__(self):
		super().__init__()
		
class Paragraph(BaseBlock):
	def __init__(self):
		super().__init__()
		
class Text(object):
	def __init__(self, text):
		self.text = text
		
class Inline(BaseInlineBlock):
	def __init__(self, feature):
		super().__init__()
		self.feature = feature
		
class Section(BaseBlock):
	def __init__(self, level, title_text_block):
		super().__init__()
		self.title = title_text_block #TODO: is this supposed to be an array?
		self.level = level


class InlineFeature(object):
	def __init__(self, name):
		self.name = name
		
feature_bold = InlineFeature("bold")
feature_italic = InlineFeature("italic")

class Link(BaseInlineBlock):
	def __init__(self, url):
		super().__init__()
		self.url = url
		
