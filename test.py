# Informal tests used while writing initial code
import sys,os

from mdl import tree_parser, parse_to_doc, doc_tree_dump
node = tree_parser.parse_file( sys.argv[1] )
tree_parser.dump(node)

print( " * * * " )

#doc = parse_to_doc.convert( node )
#doc_tree_dump.dump(doc)
