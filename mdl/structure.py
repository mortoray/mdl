from __future__ import annotations

from typing import  *
import regex as re #type: ignore
import json

from .source import Source

"""
There appears to be no way to define these cyclic types. :(

ObjectType = Dict[str, 'EntryType']
ListType = List['EntryType']
EntryType = Union[str, 'ListType', 'ObjectType']
"""
ForwardEntryType = TypeVar('ForwardEntryType')
EntryType = Union[str, float, bool, None, List[ForwardEntryType], Dict[str,ForwardEntryType]]
ObjectType = Dict[str, EntryType]
ListType = List[EntryType]

def parse_structure( data : str ) -> ObjectType:
	src = Source.with_text( data )
	return _parse_object( src, '' )
	
	
def load_structure( filename : str ) -> ObjectType:
	src = Source.with_filename( filename )
	return _parse_object( src, '' )

	
_syntax_name = re.compile( r'([\p{L}-]+):' )

def promote_value( value : str ) -> Union[str,float,bool,None]:
	# TODO: have specific conversions allowed
	try:
		return int(value)
	except ValueError:
		pass
		
	try:
		return float(value)
	except ValueError:
		pass
		
	if value == "true":
		return True
	if value == "false":
		return False
	if value == "null":
		return None
		
	return value
	
	
def _parse_object( src : Source, indent : str ) -> ObjectType:
	ret : ObjectType = {}

	value :  EntryType
	
	while True:
		src.skip_empty_lines()
		if src.is_at_end():
			break
			
		(match_indent, next_indent) = src.match_indent( indent )
		if not match_indent:
			if len(next_indent) < len(indent):
				break
			if len(next_indent) > len(indent):
				raise Exception('invalid-syntax')
			
		name_m = src.match( _syntax_name )
		assert name_m is not None
		name = name_m.group(1)
		
		src.skip_nonline_space()
		next_char = src.peek_char()
		if next_char == '\"':
			src.next_char()
			value = src.parse_string( next_char )
		else:
			parse_value = src.match_line().strip()
			if parse_value == '':
				src.skip_empty_lines()
				(match_indent, next_indent) = src.match_indent(indent)
				if not match_indent and len(next_indent) > len(indent):
					value = _parse_object(src, next_indent)
			else:
				value = promote_value(parse_value)
		ret[name] = value
		
		
	return ret

def dump_structure( obj : EntryType, indent : str = '', *, _is_initial = True ) -> str:
	text = ''
	if isinstance( obj, dict ):
		if not _is_initial:
			text += '\n' 
			indent += '\t'
			
		for key, value in obj.items():
			text += f'{indent}{key}: '
			text += dump_structure( value )
			text += '\n'
			
	elif isinstance( obj, list ):
		text += '[\n'
		for et in obj:
			text += dump_structure( et, indent  + '\t' )
			text += ',\n' 
		text += '{indent}]' 
		
	elif isinstance( obj, str ):
		text += f'"{obj}"' #TODO: escape
		
	else:
		raise Exception( "Invalid structure type", obj )
		
	return text

	
def format_json( obj : EntryType, *, pretty = False ) -> str:
	# See if standard package works for now
	kwargs : Dict[str,Any] = {
		'ensure_ascii': False,
	}
	if pretty: 
		kwargs['indent'] = "\t"
		kwargs['sort_keys'] = True
		
	return json.dumps(obj, **kwargs)

	
