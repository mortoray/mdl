# Informal tests used while writing initial code
import sys,os

from mdl import tree_parser
node = tree_parser.parse_file( sys.argv[1] )
tree_parser.dump(node)
