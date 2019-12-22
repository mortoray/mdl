from __future__ import annotations

from typing import  *
import regex as re #type: ignore

from .source import Source

"""
There appears to be no way to define these cyclic types. :(

ObjectType = Dict[str, 'EntryType']
ListType = List['EntryType']
EntryType = Union[str, 'ListType', 'ObjectType']
"""
#EntryType = Union[str, List[EntryType], Dict[str,EntryType]]
EntryType = TypeVar('EntryType')
ObjectType = Dict[str, EntryType]
ListType = List[EntryType]

def parse_structure( data : str ) -> ObjectType:
	src = Source( data )
	
	return _parse_object( src, '' )
	
	
_syntax_name = re.compile( r'([\p{L}-]+):' )

def _parse_object( src : Source, indent : str ) -> ObjectType:
	ret : ObjectType = {}

	src.skip_empty_lines()
	while not src.is_at_end():
		if not src.match_indent( indent )[0]:
			return ret
			
		name_m = src.match( _syntax_name )
		assert name_m is not None
		name = name_m.group(1)
		
		value = src.match_line().strip()
		ret[name] = value
		
		src.skip_empty_lines()
		
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
