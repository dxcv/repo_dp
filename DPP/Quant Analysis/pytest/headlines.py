# -*- coding: utf-8 -*-
"""
Created on Fri Feb 26 14:13:28 2016

@author: ngoldberger
"""

import newspaper
from bs4 import BeautifulSoup


url = 'http://www.bloomberg.com'
bloom = newspaper.build(url)
html = bloom.html
soup = BeautifulSoup(html)
headlines = {}

for link in soup.find_all('a', class_= 'top-news-v3__story__headline__link'):
    headlines.update({link.text:link.get('href')})

text = headlines.keys()

for news in text:
    print(news)

#text_file = open("Output.txt", "w")
#for news in text:
#    text_file.write("%s\n" % news)
#
#text_file.close()
#print(headlines)
#for article in bloom.articles:
#    print(article.url)
#
#article.download()
#article.parse()
#
#for x in range(0,3):
#    print bloom.articles[x].title