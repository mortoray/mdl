from . import doc_tree

def dump(node, indent = ''):
	print( get(node, indent) )

def get(node, indent = ''):
	if isinstance(node, doc_tree.Section):
		return get_section(node, indent)
	if isinstance(node, doc_tree.Inline):
		return get_inline(node, indent)
	if isinstance(node, doc_tree.Link):
		return get_link(node, indent)
		
	if isinstance(node, doc_tree.Block):
		return get_block(node, indent)
	if isinstance(node, doc_tree.Paragraph):
		return get_paragraph(node, indent)
	if isinstance(node, doc_tree.Text):
		return get_text(node, indent)
	
	raise Exception( "Unsupported type", node )

def get_all_inline(nodes):
	txt = ''
	for node in nodes:
		txt += get(node)
	return txt

def get_all(nodes, indent):
	txt = ''
	for node in nodes:
		txt += get(node, indent)
	return txt
	
def get_block(node, indent):
	txt = "{}<Block>\n".format(indent)
	for sub in node.sub:
		txt += get(sub, indent + '\t')
	return txt
	
def get_paragraph(node, indent):
	txt = "{}<Paragraph>\n".format( indent )
	indent += '\t'
	txt += indent
	for sub in node.sub:
		txt += get(sub)
	txt += '\n'
	return txt
	
def get_text(node, indent):
	return node.text
	
def get_section(node, indent):
	return '{}<Section:{}> {}\n{}'.format( indent, node.level, 
		get_all_inline(node.title), get_all(node.sub, indent + '\t') )
	
def get_inline(node, indent):
	return '%{}/{}/'.format( node.feature.name, get_all_inline(node.sub) )

def get_link(node, indent):
	return '%link{{url={}}}/{}/'.format( node.url, get_all_inline(node.sub) )
