# Abstract document tree (the document equivalent of an abstract syntax tree)

class BaseBlock(object):
	def __init__(self):
		self.sub = []
		
class BaseInlineBlock(object):
	def __init__(self):
		super().__init__()
		
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
		
