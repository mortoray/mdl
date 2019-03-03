from . import doc_tree

def dump(node, indent = ''):
	print( get(node, indent) )

def get(node, indent = ''):
	if isinstance(node, doc_tree.Block):
		return get_block(node, indent)
	if isinstance(node, doc_tree.Paragraph):
		return get_paragraph(node, indent)
	if isinstance(node, doc_tree.Text):
		return get_text(node, indent)
	if isinstance(node, doc_tree.Header):
		return get_header(node, indent)
	
	raise Exception( "Unsupported type", node )

def get_all_inline(nodes):
	txt = ''
	for node in nodes:
		txt += get(node)
	return txt
	
def get_block(node, indent):
	txt = "{}<Block>\n".format(indent)
	for sub in node.sub:
		txt += get(sub, indent + '\t')
	return txt
	
def get_paragraph(node, indent):
	txt = "{}<Paragraph>\n".format( indent )
	for sub in node.sub:
		txt += get(sub,indent + '\t')
	txt += '\n'
	return txt
	
def get_text(node, indent):
	return '{}{}'.format( indent, node.text )
	
def get_header(node, indent):
	return '{}<Heading:{}> {}\n'.format( indent, node.level, get_all_inline(node.sub) )
	
	
