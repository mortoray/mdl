# Abstract document tree (the document equivalent of an abstract syntax tree)

class TextBlock(object):
	def __init__(self):
		self.sub = []
		
class Block(object):
	def __init__(self):
		self.sub = []
		
class Paragraph(TextBlock):
	def __init__(self):
		super().__init__()
		
class Text(object):
	def __init__(self, text):
		self.text = text
		
class Header(TextBlock):
	def __init__(self, level):
		super().__init__()
		self.level = level

	
