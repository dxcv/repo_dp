# -*- coding: utf-8 -*-
"""
Created on Wed Jan 11 18:09:06 2017

@author: ngoldbergerr
"""

from collections import Counter
import pandas as pd

words = file('trump.txt','r').read().split()
counts = Counter(words)
wordRanking = pd.DataFrame(data = counts.values(), index = counts.keys(), columns = ['Count'])
#print(counts)