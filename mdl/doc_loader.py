from bs4 import BeautifulSoup
from urllib import request

def get_document_info( url ):
	response = request.urlopen( url )
	data = BeautifulSoup(response, features="html.parser")
	
	doc = {}
	for meta in data.find_all( 'meta' ):
		name = meta.get('name',None)
		if name is None:
			name = meta.get('property', None)
			
		content = meta.get('content',None)
		if content is None or name is None:
			continue
			
		if name == "og:title" or name == "twitter:title":
			doc['title'] = content
		
			
	author = data.find( itemprop = 'author' )
	if author:
		name = author.find( itemprop = 'name' )
		if name:
			doc['author'] = name.text
		
		img = author.find( 'img' )
		if img:
			doc['author_pic'] = img.get('src', None )
			
		url = author.find( itemprop = 'url' )
		if url:
			doc['author_url'] = url.get('content', None)
	
	return doc
	

	
