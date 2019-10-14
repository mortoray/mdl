from typing import  *
import regex as re #type: ignore

from .source import Source

_ObjectType = Dict[str, '_EntryType']
_ListType = List['_EntryType']
_EntryType = Union[str, _ListType, _ObjectType]

def parse_structure( data : str ) -> _ObjectType:
	src = Source( data )
	
	return _parse_object( src, '' )
	
	
_syntax_name = re.compile( r'(\p{L}+):' )

def _parse_object( src : Source, indent : str ) -> _ObjectType:
	ret = {}

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
