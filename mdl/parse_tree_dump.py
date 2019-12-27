from .parse_tree import *

"""
	Debugging and test compliance utitlity.
"""
class _dumper:
	def __init__(self, ansi = False):
		self.ansi = ansi
		
	def get( self, node : Node, indent : str = '' ) -> str:
		text = indent
		header = node.type.name
		if len(node.class_) > 0:
			header += '/' + node.class_
		text += self._bold(header)
		text += ' ' + node.text
		if node.has_args():
			text += "["
			text += ",".join( node.get_args() )
			text += "]"
		
		if node.has_annotations():
			for anno in node.iter_annotations():
				text += '\n{}\t@{}'.format( indent, self._alt(anno.class_) )
				if anno.node != None:
					text += '\n' + self.get( anno.node, indent + '\t\t' )
		if node.has_attr():
			text += '\n' + indent + '\tattrs\n'
			for attr in node.iter_attr():
				text += self.get( attr, indent + '\t\t' )
		else:
			text += '\n'
					
		indent += "\t"
		for sub in node.iter_sub():
			text += self.get( sub, indent )

		return text

	def _bold(self, text : str) -> str:
		if not self.ansi:
			return text
		return '\x1b[1m{}\x1b[m'.format(text)

	def _alt(self, text : str) -> str:
		if not self.ansi:
			return text
		return '\x1b[96m{}\x1b[m'.format(text)
		
		
def dump( node : Node ) -> None:
	print( _dumper( ansi = True ).get( node ) )
	
def get_dump( node : Node ) -> str:
	return _dumper().get( node )
