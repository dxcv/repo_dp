# -*- coding: utf-8 -*-
"""
Created on Fri Dec 18 11:19:52 2015

@author: ngoldberger
"""

import pandas as pd  
import matplotlib.pyplot as plt  
  
# Due to an agreement with the ChessGames.com admin, I cannot make the data  
# for this plot publicly available. This function reads in and parses the  
# chess data set into a tabulated pandas DataFrame.  
chess_data = read_chess_data()  
  
# You typically want your plot to be ~1.33x wider than tall.  
# Common sizes: (10, 7.5) and (12, 9)  
plt.figure(figsize=(12, 9))  
  
# Remove the plot frame lines. They are unnecessary chartjunk.  
ax = plt.subplot(111)  
ax.spines["top"].set_visible(False)  
ax.spines["right"].set_visible(False)  
  
# Ensure that the axis ticks only show up on the bottom and left of the plot.  
# Ticks on the right and top of the plot are generally unnecessary chartjunk.  
ax.get_xaxis().tick_bottom()  
ax.get_yaxis().tick_left()  
  
# Make sure your axis ticks are large enough to be easily read.  
# You don't want your viewers squinting to read your plot.  
plt.xticks(fontsize=14)  
plt.yticks(range(5000, 30001, 5000), fontsize=14)  
  
# Along the same vein, make sure your axis labels are large  
# enough to be easily read as well. Make them slightly larger  
# than your axis tick labels so they stand out.  
plt.xlabel("Elo Rating", fontsize=16)  
plt.ylabel("Count", fontsize=16)  
  
# Plot the histogram. Note that all I'm passing here is a list of numbers.  
# matplotlib automatically counts and bins the frequencies for us.  
# "#3F5D7D" is the nice dark blue color.  
# Make sure the data is sorted into enough bins so you can see the distribution.  
plt.hist(list(chess_data.WhiteElo.values) + list(chess_data.BlackElo.values),  
         color="#3F5D7D", bins=100)  
  
# Always include your data source(s) and copyright notice! And for your  
# data sources, tell your viewers exactly where the data came from,  
# preferably with a direct link to the data. Just telling your viewers  
# that you used data from the "U.S. Census Bureau" is completely useless:  
# the U.S. Census Bureau provides all kinds of data, so how are your  
# viewers supposed to know which data set you used?  
plt.text(1300, -5000, "Data source: www.ChessGames.com | "  
         "Author: Randy Olson (randalolson.com / @randal_olson)", fontsize=10)  
  
# Finally, save the figure as a PNG.  
# You can also save it as a PDF, JPEG, etc.  
# Just change the file extension in this call.  
# bbox_inches="tight" removes all the extra whitespace on the edges of your plot.  
plt.savefig("chess-elo-rating-distribution.png", bbox_inches="tight");  