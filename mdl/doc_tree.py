# Abstract document tree (the document equivalent of an abstract syntax tree)

class InlineBlock(object):
	def __init__(self):
		self.sub = []
		
class Block(object):
	def __init__(self):
		self.sub = []
		
class Paragraph(InlineBlock):
	def __init__(self):
		super().__init__()
		
class Text(object):
	def __init__(self, text):
		self.text = text
		
class Inline(InlineBlock):
	def __init__(self):
		super().__init__()
		
class Section(Block):
	def __init__(self, level, title_text_block):
		super().__init__()
		self.title = title_text_block
		self.level = level

	
