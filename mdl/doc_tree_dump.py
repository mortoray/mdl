from . import doc_tree
from typing import *

def dump(node, indent = ''):
	print( get(node, indent) )

def get(node, indent = ''):
	if node == None:
		return '** NONE **'

	if isinstance(node, doc_tree.Section):
		return get_section(node, indent)
	if isinstance(node, doc_tree.Inline):
		return get_inline(node, indent)
	if isinstance(node, doc_tree.Link):
		return get_link(node, indent)
	if isinstance(node, doc_tree.Note):
		return get_note(node, indent)
	if isinstance(node, doc_tree.List):
		return get_list(node, indent)
	if isinstance(node, doc_tree.ListItem):
		return get_list_item(node, indent)
		
	if isinstance(node, doc_tree.Block):
		return get_block(node, indent)
	if isinstance(node, doc_tree.Text):
		return get_text(node, indent)
	if isinstance(node, doc_tree.Paragraph):
		return get_paragraph(node, indent)
	if isinstance(node, doc_tree.Embed):
		return get_embed(node, indent)
	if isinstance(node, doc_tree.Code):
		return get_code(node, indent)
	
	raise Exception( "Unsupported type", node )

def get_all_inline(nodes):
	if nodes == None:
		return ''
		
	txt = ''
	for node in nodes:
		txt += get(node)
	return txt

def get_all(nodes, indent):
	txt = ''
	for node in nodes:
		txt += get(node, indent)
	return txt
	
def _get_sub(node, indent):
	indent += '\t'
	txt = ""
	for sub in node.iter_sub():
		txt += get(sub, indent)
	txt += '\n'
	return txt

def get_block(node, indent):
	txt = "{}<Block:{}>\n".format( indent, node.class_.name )
	txt += _get_sub(node, indent)
	return txt
	
def get_paragraph(node, indent):
	txt = "{}<Paragraph>\n".format( indent )
	txt += _get_sub(node, indent)
	return txt
	
def get_text(node, indent):
	return indent + node.text

def get_code(node : doc_tree.Code, indent):
	return "{}<Code:{}>\n{}{}\n".format( indent, node.class_, indent + "\t", 
		node.text.replace( "\n", "\n{}".format( indent + "\t") ) )
		
def get_flow(nodes : Sequence[doc_tree.BlockNode], indent : str) -> str:
	text = ''
	for node in nodes:
		text += get( node, indent )
	return text

def get_section(node : doc_tree.Section, indent : str) -> str:
	text = '{}<Section:{}>\n'.format( indent, node.level )
	if node.title:
		text += '{}\n'.format( get_flow(node.title, indent + '\t|') )
	text += get_all(node._sub, indent + '\t')
	return text
	
def get_inline(node, indent):
	return '%{}/{}/'.format( node.feature.name, get_all_inline(node._sub) )

def get_link(node, indent):
	return '%link{{url={}}}/{}/'.format( node.url, get_all_inline(node._sub) )

def get_note(node, indent):
	return '^{{{}}}'.format( get_all_inline(node._sub) )
	
def get_list(node, indent):
	return '{}<List>\n{}'.format( indent, get_all(node._sub, indent + '\t') )
	
def get_list_item(node, indent):
	return '{}<ListItem>\n{}'.format( indent, get_all(node._sub, indent + '\t') )

def get_embed(node, indent):
	return '{}<Embed:{}> {}'.format( indent, node.class_.name, node.url )
