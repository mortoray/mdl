from __future__ import annotations

from typing import  *
import regex as re #type: ignore
import json

from .source import Source, SourceLocation

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

def structure_parse( data : str, location : Optional[SourceLocation] = None ) -> ObjectType:
	return _parse_source( Source.with_text( data, location ) )
	
def structure_parse_list( data : str, location : Optional[SourceLocation] = None ) -> ListType:
	return _parse_inline_list( Source.with_text( data, location ) )

def structure_load( filename : str ) -> ObjectType:
	return _parse_source( Source.with_filename( filename ) )


def _parse_source( src : Source ) -> ObjectType:
	obj = _parse_object( src, '' )
	if not isinstance(obj, dict):
		raise Exception("root-element-not-list")
	return obj

	
_syntax_name = re.compile( r'([\p{L}\p{N}-_.@]+)\s*([:=])' )
_syntax_comment = re.compile( r'([\p{Space_Separator}\t\s]*)#[^\r\n]*' )
_syntax_space_or_comment = re.compile( r'[\p{Space_Separator}\t#\s]' )
_syntax_line_or_comment = re.compile( r'[\r\n#]' )


class CallList(list):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		
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
	

def _parse_inline_value( src : Source ) -> Optional[EntryType]:
	next_char = src.peek_char()
	if next_char == '\"':
		src.next_char()
		return src.parse_string( next_char )
		
	if next_char == '[':
		src.next_char()
		return _parse_inline_list( src, ']' )
		
	if next_char == '(':
		src.next_char()
		return CallList(_parse_inline_list( src, ')' ))
		
	if next_char == '{':
		src.next_char()
		return _parse_inline_map( src, '}' )
		
	return None
	
	
def _parse_line_value( src : Source, indent : Optional[str] = None ) -> EntryType:
	ivalue = _parse_inline_value( src )
	line_value = src.parse_string_to( re = _syntax_line_or_comment ).strip()
	
	if not ivalue is None:
		if line_value != '':
			src.fail( 'trailing-line-value' )
		return ivalue
		
	if indent is None:
		raise Exception("no-multiline-allowed-here")
	if line_value == '':
		_skip_empty_lines(src)
		(match_indent, next_indent) = src.match_indent(indent)
		if not match_indent and len(next_indent) > len(indent):
			return _parse_object(src, next_indent)
		raise Exception("missing-value")
		
	return promote_value(line_value)

	
def _parse_space_value( src : Source, terminal : Optional[str] = None ) -> EntryType:
	ivalue = _parse_inline_value( src )
	if not ivalue is None:
		return ivalue
		
	value = src.parse_string_to( char = terminal, re = _syntax_space_or_comment, consume_terminal = False )
	return promote_value( value )
	
	
def _parse_inline_list( src : Source, terminal : Optional[str] = None, end_on_line : bool = False ) -> ListType:
	ret_list : ListType = []
	
	while True:
		if end_on_line:
			src.skip_nonline_space()
		else:
			src.skip_space()
		if src.is_at_end():
			if terminal is None:
				break
			src.fail( 'incomplete-inline-list' )
			
		next_char = src.peek_char()
		if next_char == terminal:
			src.next_char()
			break
			
		if end_on_line and next_char in ['\r','\n']:
			break
			
		value = _parse_space_value( src, terminal )
		ret_list.append(value)
	return ret_list
	
	
def _parse_inline_map( src : Source, terminal : Optional[str] = None ) -> ObjectType:
	ret : ObjectType = {}
	
	while True:
		src.skip_space()
		if src.is_at_end():
			if terminal is None:
				break
			src.fail( 'incomplete-inline-set' )
			
		next_char = src.peek_char()
		if next_char == terminal:
			src.next_char()
			break
			
		name, value = _parse_named(src, terminal = '}')
		ret[name] = value
			
		
	return ret
	
def _skip_empty_lines( src : Source ) -> None:
	while True:
		src.skip_empty_lines()
		if src.match( _syntax_comment ):
			continue
		break
	
def _parse_object( src : Source, indent : str ) -> EntryType:
	ret_obj : ObjectType = {}
	ret_list : ListType = []
	ret : Union[ObjectType,ListType] = ret_obj
	is_array = False
	
	while True:
		_skip_empty_lines(src)
		if src.is_at_end():
			break
			
		(match_indent, next_indent) = src.match_indent( indent )
		if not match_indent:
			if len(next_indent) < len(indent):
				break
			if len(next_indent) > len(indent):
				raise Exception('invalid-syntax')
			
		next_char = src.peek_char()
		if next_char in ['-','=']:
			src.next_char()
			if not is_array:
				ret = ret_list
				is_array = True
			src.skip_nonline_space()
			if next_char == '-':
				ret_list.append( _parse_line_value(src, indent) )
			else:
				ret_list.append( CallList(_parse_inline_list(src, end_on_line=True)) )
				
		elif is_array:
			raise Exception('mixing-non-array-item')
			
		else:
			name, value = _parse_named(src, indent)
			ret_obj[name] = value
		
	return ret

	
def _parse_named( src : Source, indent : Optional[str] = None, terminal : Optional[str] = None ) -> Tuple[str, EntryType]:
	name_m = src.match( _syntax_name )
	if name_m is None:
		src.fail('expecting-a-name')
	name = name_m.group(1)
	op = name_m.group(2)

	src.skip_nonline_space()
	if op == ':':
		if indent is not None:
			value = _parse_line_value(src, indent)
		else:
			value = _parse_space_value(src, terminal)
	elif op == '=':
		value = CallList(_parse_inline_list(src, end_on_line = True))
	else:
		raise Exception('unreachable')
		
	return (name, value)
	

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
			
	elif isinstance( obj, CallList ):
		text += f'{indent}(\n'
		for et in obj:
			text += dump_structure( et, indent  + '\t' )
			text += ',\n' 
		text += f'{indent})' 
	
	elif isinstance( obj, list ):
		text += f'{indent}[\n'
		for et in obj:
			text += dump_structure( et, indent  + '\t' )
			text += ',\n' 
		text += f'{indent}]' 
		
	elif isinstance( obj, str ):
		text += f'{indent}"{obj}"' #TODO: escape
		
	elif isinstance( obj, bool ):
		text += indent + ('true' if obj else 'false')
		
	elif isinstance( obj, float ) or isinstance( obj, int ):
		text += f'{indent}{obj}'
		
	elif obj is None:
		text += f'{indent}null'
		
	else:
		raise Exception( "Invalid structure type", obj )
		
	return text

	
def structure_format_json( obj : EntryType, *, pretty = False ) -> str:
	# See if standard package works for now
	kwargs : Dict[str,Any] = {
		'ensure_ascii': False,
	}
	if pretty: 
		kwargs['indent'] = "\t"
		kwargs['sort_keys'] = True
		
	return json.dumps(obj, **kwargs)

	
