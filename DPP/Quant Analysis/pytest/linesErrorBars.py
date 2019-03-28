# -*- coding: utf-8 -*-
"""
Created on Fri Dec 18 11:18:32 2015

@author: ngoldberger
"""

import pandas as pd  
import matplotlib.pyplot as plt  
from scipy.stats import sem  
  
# This function takes an array of numbers and smoothes them out.  
# Smoothing is useful for making plots a little easier to read.  
def sliding_mean(data_array, window=5):  
    data_array = array(data_array)  
    new_list = []  
    for i in range(len(data_array)):  
        indices = range(max(i - window + 1, 0),  
                        min(i + window + 1, len(data_array)))  
        avg = 0  
        for j in indices:  
            avg += data_array[j]  
        avg /= float(len(indices))  
        new_list.append(avg)  
          
    return array(new_list)  
  
# Due to an agreement with the ChessGames.com admin, I cannot make the data  
# for this plot publicly available. This function reads in and parses the  
# chess data set into a tabulated pandas DataFrame.  
chess_data = read_chess_data()  
  
# These variables are where we put the years (x-axis), means (y-axis), and error bar values.  
# We could just as easily replace the means with medians,  
# and standard errors (SEMs) with standard deviations (STDs).  
years = chess_data.groupby("Year").PlyCount.mean().keys()  
mean_PlyCount = sliding_mean(chess_data.groupby("Year").PlyCount.mean().values,  
                             window=10)  
sem_PlyCount = sliding_mean(chess_data.groupby("Year").PlyCount.apply(sem).mul(1.96).values,  
                            window=10)  
  
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
  
# Limit the range of the plot to only where the data is.  
# Avoid unnecessary whitespace.  
plt.ylim(63, 85)  
  
# Make sure your axis ticks are large enough to be easily read.  
# You don't want your viewers squinting to read your plot.  
plt.xticks(range(1850, 2011, 20), fontsize=14)  
plt.yticks(range(65, 86, 5), fontsize=14)  
  
# Along the same vein, make sure your axis labels are large  
# enough to be easily read as well. Make them slightly larger  
# than your axis tick labels so they stand out.  
plt.ylabel("Ply per Game", fontsize=16)  
  
# Use matplotlib's fill_between() call to create error bars.  
# Use the dark blue "#3F5D7D" as a nice fill color.  
plt.fill_between(years, mean_PlyCount - sem_PlyCount,  
                 mean_PlyCount + sem_PlyCount, color="#3F5D7D")  
  
# Plot the means as a white line in between the error bars.   
# White stands out best against the dark blue.  
plt.plot(years, mean_PlyCount, color="white", lw=2)  
  
# Make the title big enough so it spans the entire plot, but don't make it  
# so big that it requires two lines to show.  
plt.title("Chess games are getting longer", fontsize=22)  
  
# Always include your data source(s) and copyright notice! And for your  
# data sources, tell your viewers exactly where the data came from,  
# preferably with a direct link to the data. Just telling your viewers  
# that you used data from the "U.S. Census Bureau" is completely useless:  
# the U.S. Census Bureau provides all kinds of data, so how are your  
# viewers supposed to know which data set you used?  
plt.xlabel("\nData source: www.ChessGames.com | "  
           "Author: Randy Olson (randalolson.com / @randal_olson)", fontsize=10)  
  
# Finally, save the figure as a PNG.  
# You can also save it as a PDF, JPEG, etc.  
# Just change the file extension in this call.  
# bbox_inches="tight" removes all the extra whitespace on the edges of your plot.  
plt.savefig("chess-number-ply-over-time.png", bbox_inches="tight");  