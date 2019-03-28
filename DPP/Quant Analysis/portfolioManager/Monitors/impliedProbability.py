# -*- coding: utf-8 -*-
"""
Created on Fri Apr 08 16:11:38 2016

@author: ngoldberger
"""
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
#import numpy as np
from tia.bbg import LocalTerminal
from calendar import monthrange
import pygal
from pygal.style import RedBlueStyle
from pygal.style import Style


class implied_probability(object):

    def __init__(self):
        self.d = datetime.datetime.now()
        self.date = self.d.strftime("%m/%Y")
        
    def defineInstruments(self,date):
        self.futureYearNumber = []
        self.futureMonthLetter = {'1': 'F', '2': 'G', '3': 'H', '4': 'J',
                                  '5': 'K', '6': 'M', '7': 'N', '8': 'Q',
                                  '9': 'U', '10': 'V', '11': 'X', '12': 'Z'}
        self.futureCode = ['FF' + self.futureMonthLetter[str(x)] for x in range(1,13)]
        month = int(date[0:2])
        year = int(date[6])
        for i in range(1,13):
            if i < month:
                aux = 1
            else:
                aux = 0

            self.futureYearNumber.append(year + aux)

        self.futureName = [self.futureCode[i]+str(self.futureYearNumber[i])+" Comdty" for i in range(0,12)]

    def downloadData(self):
        self.response = LocalTerminal.get_reference_data(self.futureName, ['px_last'])

    def getProbabilities(self):
        scenario_1 = [1,4,7,12] # Meeeting in a month where the previous month had a meeting
        scenario_2 = [3,6,11] # Meeting in a month where the previous wasn't a meeting
        scenario_3 = [2,5,8,10] # No meeting
        hike = 0
        noHike = 0
        cut = 0
        FOMCmeetingDates = [27, 16, 27, 15, 27, 21, 2, 14] # This has to be updated every year
        self.probabilities = pd.DataFrame(columns = ['hike','no hike','cut'])
        y = 0
        for x in range(1,13):
            N = float(monthrange(int(self.date[3:8]),x)[1])
            hike = 0
            noHike = 0
            cut = 0
            if x in scenario_3:
                continue
            elif x in scenario_1:
                M = float(FOMCmeetingDates[y]-1)
                if x == 12:
                    FFERend = 100 - self.response.as_frame()['px_last'][0]
                else:
                    FFERend = 100 - self.response.as_frame()['px_last'][x]
                IR = 100 - self.response.as_frame()['px_last'][x-1]
                FFERstart = (N/M)*(IR - FFERend*((N-M)/N))
                hike = (FFERend - FFERstart)/0.25
                noHike = 1 - hike
                if hike < 0:
                    cut = - hike
                    hike = 0
                    noHike = 1 - cut

            elif x in scenario_2:   
                M = float(FOMCmeetingDates[y]-1)
                FFERstart = 100 - self.response.as_frame()['px_last'][x-2]
                IR = 100 - self.response.as_frame()['px_last'][x-1]
                FFERend = (N/(N-M))*(IR - FFERend*(M/N))
                hike = (FFERend - FFERstart)/0.25
                noHike = 1 - hike
                if hike < 0:
                    cut = - hike
                    hike = 0
                    noHike = 1 - cut
            else:
                M = float(FOMCmeetingDates[y]-1)
                FFERstart = 100 - self.response.as_frame()['px_last'][x-2]
                FFERend = 100 - self.response.as_frame()['px_last'][x]
                hike = (FFERend - FFERstart)/0.25
                noHike = 1 - hike
                if hike < 0:                
                    cut = - hike             
                    hike = 0                    
                    noHike = 1 - cut
                    
            month_prob = pd.DataFrame([(hike, noHike, cut)], columns = ['hike','no hike','cut'])
            self.probabilities = pd.concat([self.probabilities, month_prob])

            y += 1

        self.probabilities.index = [datetime.date(2018,09,09), # This has to be updated every month!
                                    datetime.date(2019,04,01),
                                    datetime.date(2019,03,01),
                                    datetime.date(2019,02,01),
                                    datetime.date(2019,01,02),
                                    datetime.date(2018,12,21),
                                    datetime.date(2018,11,01),  
                                    datetime.date(2018,10,01)]

        self.probabilities.sort_index(inplace = True)

        return self.probabilities

    def buildTree(self):
        jumpRate = 0.25
        currentRate = LocalTerminal.get_reference_data('FDTR Index', 'px_last').as_frame()['px_last']['FDTR Index']
        probabilities = self.probabilities
        tree = [{str(currentRate): 1}]

        for p_hike, p_nohike, p_cut in probabilities.values:
            new_branch = {}

            for rates_prev, prob_prev in tree[-1].iteritems():
                rate_up = str(float(rates_prev) + jumpRate)
                rate_down = str(float(rates_prev) - jumpRate)

                if rate_up not in new_branch: new_branch[rate_up] = 0
                if rate_down not in new_branch: new_branch[rate_down] = 0
                if rates_prev not in new_branch: new_branch[rates_prev] = 0

                new_branch[rate_up] += prob_prev*p_hike
                new_branch[rates_prev] += prob_prev*p_nohike
                new_branch[rate_down] += prob_prev*p_cut

            tree.append(new_branch)
        return tree
        
    def treeToDF(self, tree):
        treeAsFrame = pd.DataFrame()
        for branch in tree:
            newColumn = pd.Series(branch.values(), index = [float(tasa) for tasa in branch.keys()])
            treeAsFrame = pd.concat([treeAsFrame, newColumn], axis = 1)

        treeAsFrame = treeAsFrame.sort_index(ascending = False)
#        treeAsFrame = treeAsFrame.where((pd.notnull(treeAsFrame)), "")
        months = ["Now"]
        for dates in self.probabilities.index:
            months.append(dates.strftime('%B'))

        treeAsFrame.columns = months
        treeAsFrame = treeAsFrame.multiply(100)
        pd.options.display.float_format = '{:,.1f}'.format
        return treeAsFrame

    def graphBars(self,treeDF):
        data = treeDF.replace(to_replace = "", value = 0)
        data = data[::-1]
        fig, ax = plt.subplots()
        index = data.index
        bar_width = 0.025
        aux = 0
        start = 8
        end = 13
        data_start = data.index.values[start]
        data_end = data.index.values[end-1]
        for month in data.columns[1:]:
            plt.bar(index.values[start:end]+bar_width*aux, data[month][data_start:data_end].values, bar_width, color=cm.RdYlBu(1.*aux/len(data.columns[1:])), edgecolor = 'w')
            aux += 1
        labels = []
        for i in index.values[start:end]:
            labels.append(i)        
        plt.xlabel('Fed Funds Target Rate (Upper Bound)',fontsize = 18)
        plt.ylabel('Probability',fontsize = 18)
        plt.title('Fed Hike Implied Probability',fontsize = 20)
        plt.xticks(index[start:end]+0.1, labels,fontsize = 16)
        plt.yticks(fontsize = 16)
        plt.legend(data.columns[1:],fontsize = 14)
        plt.tight_layout()
        fig.set_size_inches(11.5, 7.5)
        plt.show()

if __name__ == '__main__':
    ip = implied_probability()
    ip.defineInstruments(ip.date)
    ip.downloadData()
    prob = ip.getProbabilities()
    prob_tree = ip.buildTree()
    treeAsFrame = ip.treeToDF(prob_tree)
#    ip.graphBars(treeAsFrame)

    treeAsFrameClean = treeAsFrame.where((pd.notnull(treeAsFrame)), None).sort_index()
    treeAsFrameClean[treeAsFrameClean == 0.0] = None
    stackedBar_chart = pygal.StackedBar(style=RedBlueStyle) #show_legend=False
    tree_transpose = treeAsFrameClean.transpose()
    for column in tree_transpose:
        stackedBar_chart.add(str(column), tree_transpose[:-1][column].values)
    stackedBar_chart.title = 'Fed Hike Implied Probability'
    stackedBar_chart.x_labels = tree_transpose[:-1].index.values
    pygal.style.Style.font_family = 'Calibri Light'
    pygal.style.Style.label_font_size = 14
    pygal.style.Style.major_label_font_size = 14
    pygal.style.Style.title_font_size = 18
    stackedBar_chart.render_to_file('stackedBar_chart.svg')
    
    bar_chart = pygal.Bar()
    for column in treeAsFrameClean.iloc[:,:-1]:
        bar_chart.add(str(column), treeAsFrameClean[column][0.5:1.75].values)
    bar_chart.title = 'Fed Hike Implied Probability'
    bar_chart.x_labels = treeAsFrameClean[0.5:1.75].index.values
    pygal.style.Style.font_family = 'Calibri Light'
    pygal.style.Style.label_font_size = 14
    pygal.style.Style.major_label_font_size = 14
    pygal.style.Style.title_font_size = 18
    bar_chart.render_to_file('bar_chart.svg')