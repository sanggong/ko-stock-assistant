import mplfinance as mpf
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from datetime import datetime
import pandas as pd
import numpy as np
import math

class Plot:

    color = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
             '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

    def __init__(self):
        pass

    def show(self):
        plt.show()

    def plot_ohlc_all(self, data):
        '''
        :param data: [{code:code0, df:dataframe0(ohlc)}, {code:code1, df:dataframe1(ohlc)}, ...]
        :return:
        '''
        page, limit = 0, min(8, len(data))   # page starts 0
        max_page = math.ceil(len(data) / limit)
        fig = mpf.figure(figsize=(12,9), style='yahoo')

        axes = []
        for i in range(limit):
            ax = fig.add_subplot(2, 4, i+1)
            axes.append(ax)
            mpf.plot(data[i]['df'], ax=ax, type='candle', axtitle=data[i]['code'])

        def button_prev(event):
            nonlocal page, limit, max_page
            nonlocal data
            nonlocal axes, axtext
            page = (page - 1) if page > 0 else max_page - 1
            replot_ohlc(data, axes, page, limit, axtext)

        def button_next(event):
            nonlocal page, limit, max_page
            nonlocal data
            nonlocal axes, axtext
            page = (page + 1) % max_page
            replot_ohlc(data, axes, page, limit, axtext)

        def replot_ohlc(data, axes, page, limit, axtext):
            axtext.clear()
            axtext.text(0.4, 0.2, '{:2d} / {:2d}'.format(page+1, max_page))

            for i, ax in enumerate(axes):
                ax.clear()
            for i, ax in enumerate(axes):
                idx = i + (page * limit)
                if idx >= len(data):
                    break
                mpf.plot(data[idx]['df'], ax=ax, type='candle', axtitle=data[idx]['code'])

        # make prev or next button
        axprev = fig.add_axes([0.7, 0.05, 0.1, 0.075])
        axnext = fig.add_axes([0.81, 0.05, 0.1, 0.075])
        bprev = Button(axprev, '◀')
        bnext = Button(axnext, '▶')
        bnext.on_clicked(button_next)
        bprev.on_clicked(button_prev)

        # make current page representation
        axtext = fig.add_axes([0.5, 0.05, 0.1, 0.075])
        axtext.text(0.4, 0.2, '{:2d} / {:2d}'.format(page+1, max_page))

        mpf.show()


    def plot_profit(self, day, groups, means, gmeans):
        '''
        Set plot about profit mean and geometric mean
        day : x-axis
        means, gmeans : y-axis
        '''
        plt.figure('Profit Graph')
        plt.title('Profit Graph')
        plt.xlabel('Days')
        plt.legend()
        for i, mean, gmean, group in enumerate(zip(means, gmeans, groups)):
            plt.plot(day, mean, color=Plot.color[i], label=f"[G_{group}] mean", linestyle='-')
            plt.plot(day, gmean, color=Plot.color[i], label=f"[G_{group}] g_mean", linestyle='-.')

    def plot_profit_stddev(self, day, groups, stddevs):
        '''
        Set plot about profit standard deviation
        '''
        plt.figure('Stddev Graph')
        plt.title('Stddev Graph')
        plt.xlabel('Days')
        plt.legend()
        for i, stddev, group in enumerate(zip(stddevs, groups)):
            plt.plot(day, stddev, color=Plot.color[i], label=f"[G_{group}] stddev")
