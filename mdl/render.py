import abc

class Writer(abc.ABC):
	def __init__(self):
		pass
		
	@abc.abstractmethod
	def render(self, node):
		pass

		
