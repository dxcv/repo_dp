# -*- coding: utf-8 -*-
"""
Created on Thu Feb 25 14:41:05 2016

@author: ngoldberger
"""

"""
Using custom colors
====================
Using the recolor method and custom coloring functions.
"""

import numpy as np
from PIL import Image
from os import path
import matplotlib.pyplot as plt
import random

from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator


def grey_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
    return "hsl(0, 0%%, %d%%)" % random.randint(60, 100)

d = path.dirname(__file__)

# read the mask image
# Mask provides a figure for the wordcloud
mask = np.array(Image.open(path.join(d, "map.png")))

# read the text to create the cloud
# The text is the input to create the wordcloud
text = open("Output.txt").read()

# Preprocessing the text to replace words
#text = text.replace("HAN", "Han")
#text = text.replace("LUKE'S", "Luke")

# Adding specific stopwords, these are words we will skip
stopwords = STOPWORDS.copy()
stopwords.add("World")
stopwords.add("am")
stopwords.add("EST")


# The actual creation of the cloud
wc = WordCloud(background_color = "black", max_words=1000, mask=mask, stopwords=stopwords, margin=10,
               random_state=42).generate(text)

image_colors = ImageColorGenerator(mask)
               
# Store default colored image
default_colors = wc.to_array()
#plt.title("Custom colors")
#plt.imshow(wc.recolor(color_func=grey_color_func, random_state=3))
#wc.to_file("a_new_hope.png")
#plt.axis("off")
plt.figure(figsize=(9,12))
#plt.title("Default colors")
#plt.imshow(default_colors)
plt.imshow(wc.recolor(color_func=image_colors))
plt.axis("off")
plt.show()