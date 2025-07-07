from typing import cast
from bs4 import BeautifulSoup
from bs4.element import Tag
from urllib import request

def get_document_info( url ):
	response = request.urlopen( url )
	data = BeautifulSoup(response, features="html.parser")
	
	doc = {}
	for meta in data.find_all( 'meta' ):
		if not isinstance(meta, Tag):
			continue
			
		name = meta.get('name',None)
		if name is None:
			name = meta.get('property', None)
			
		content = meta.get('content',None)
		if content is None or name is None:
			continue
			
		if name == "og:title" or name == "twitter:title":
			doc['title'] = content
		
			
	author = cast( Tag, data.find( itemprop = 'author' ))
	if author:
		author_name = cast( Tag, author.find( itemprop = 'name' ))
		if name:
			doc['author'] = author_name.text
		
		img = cast( Tag, author.find( 'img' ) )
		if img:
			doc['author_pic'] = cast( str, img.get('src', None ))
			
		url = cast( Tag, author.find( itemprop = 'url' ))
		if url:
			doc['author_url'] = cast( str, url.get('content', None))
	
	return doc
	

	
