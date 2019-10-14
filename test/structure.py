from mdl import structure

def test_basic():
	obj = structure.parse_structure( "value: one" )
	assert obj['value'] == 'one'

def test_more():
	obj = structure.parse_structure( """
one: 1

two:   hello  
three: a b c 
""" )
	assert obj['one'] == '1'
	assert obj['two'] == 'hello'
	assert obj['three'] == 'a b c'
	
